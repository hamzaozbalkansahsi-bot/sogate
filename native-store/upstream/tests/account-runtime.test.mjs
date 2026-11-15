import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn, spawnSync} from 'node:child_process';
import {readFile, writeFile, mkdtemp, mkdir, rm, stat} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import net from 'node:net';
import {randomBytes} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const php = process.env.PHP_BINARY || 'php';
const probe = spawnSync(php, ['-r', 'exit(in_array("sqlite", PDO::getAvailableDrivers(), true) ? 0 : 1);'], {encoding: 'utf8'});
const missing = probe.status !== 0 ? 'PHP with PDO SQLite unavailable; account HTTP runtime not verified' : false;
const phpQuote = value => "'" + value.replaceAll('\\', '\\\\').replaceAll("'", "\\'") + "'";

test('real account HTTP runtime isolates users, sessions and durable state', {skip: missing}, async t => {
  const temporary = await mkdtemp(path.join(os.tmpdir(), 'nodeno-account-'));
  const publicRoot = path.join(temporary, 'public');
  const storageRoot = path.join(temporary, 'persistent-account-data');
  await mkdir(publicRoot);
  const source = JSON.parse(await readFile(path.join(root, 'data/catalog-source.json'), 'utf8'));
  const ids = source.products.map(product => String(product.id));
  assert.equal(ids.length, 667);
  await writeFile(path.join(temporary, 'catalog.json'), JSON.stringify({products: ids.map(id => ({id}))}));
  const router = path.join(temporary, 'router.php');
  await writeFile(router, `<?php
declare(strict_types=1);
ini_set('display_errors', '0');
set_error_handler(static function(int $severity, string $message, string $file, int $line): bool {
  if (!(error_reporting() & $severity)) return false;
  throw new ErrorException($message, 0, $severity, $file, $line);
});
function nodenoRespond(string $body, int $status = 200, string $type = 'application/json; charset=utf-8', array $extra = []): void {
  http_response_code($status);
  header('Content-Type: ' . $type);
  foreach ($extra as $key => $value) header($key . ': ' . $value);
  if ($_SERVER['REQUEST_METHOD'] !== 'HEAD') echo $body;
}
require ${phpQuote(path.join(root, 'hosting/account.php'))};
$catalog = json_decode(file_get_contents(${phpQuote(path.join(temporary, 'catalog.json'))}), true, 512, JSON_THROW_ON_ERROR);
$storage = isset($_GET['unsafe']) ? __DIR__ . '/public/forbidden-account-data' : ${phpQuote(storageRoot)};
if (!nodenoHandleAccountRequest(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), $_SERVER['REQUEST_METHOD'], $catalog, $storage)) nodenoRespond('{"error":"not_found"}', 404);
`);
  const listener = net.createServer();
  await new Promise(resolve => listener.listen(0, '127.0.0.1', resolve));
  const port = listener.address().port;
  await new Promise(resolve => listener.close(resolve));
  const origin = `http://127.0.0.1:${port}`;
  let server, stopped, output = '';
  async function start() {
    server = spawn(php, ['-d', 'display_errors=0', '-S', `127.0.0.1:${port}`, '-t', publicRoot, router], {cwd: root, stdio: ['ignore', 'pipe', 'pipe']});
    stopped = new Promise(resolve => server.once('exit', resolve));
    server.stdout.on('data', chunk => {output += chunk;});
    server.stderr.on('data', chunk => {output += chunk;});
    for (let attempt = 0; attempt < 60; attempt++) {
      try {await fetch(origin + '/api/account'); return;} catch {await new Promise(resolve => setTimeout(resolve, 50));}
    }
    throw new Error('PHP server did not start: ' + output);
  }
  async function stop() {if (server) {server.kill(); await stopped; server = null;}}
  const client = () => ({cookie: '', csrf: ''});
  async function request(jar, route, {method = 'GET', body, headers = {}, raw} = {}) {
    if (route === '/api/account/register' && body && !Object.hasOwn(body, 'acceptMembership')) {
      const terms = await request(jar, '/api/account/membership-terms?lang=tr');
      assert.equal(terms.status, 200);
      body = {...body, acceptMembership: true, membershipVersion: terms.data.version, membershipHash: terms.data.hash, membershipLocale: terms.data.locale};
    }
    const mutation = !['GET', 'HEAD'].includes(method);
    const response = await fetch(origin + route, {method, headers: {
      ...(jar.cookie ? {Cookie: jar.cookie} : {}),
      ...(mutation ? {Origin: origin, 'Content-Type': 'application/json', 'X-CSRF-Token': jar.csrf} : {}), ...headers,
    }, ...(mutation ? {body: raw ?? JSON.stringify(body ?? {})} : {})});
    const cookie = response.headers.get('set-cookie');
    if (cookie) jar.cookie = cookie.split(';')[0];
    const text = await response.text();
    let data;
    try {data = text ? JSON.parse(text) : null;} catch {assert.fail(`Invalid JSON ${response.status}: ${text}\n${output}`);}
    if (data?.csrfToken) jar.csrf = data.csrfToken;
    return {status: response.status, headers: response.headers, data};
  }
  async function completeVerifiedFixture(jar,identity,intent='login'){
    // Only test-owned SQLite is seeded after token verification is covered by
    // social-auth.test.mjs. No fake provider endpoint exists in production.
    const account=await request(jar,'/api/account'),browser=randomBytes(32).toString('hex');
    const program=`require ${phpQuote(path.join(root,'hosting/account.php'))};$fixture=json_decode($argv[1],true);$db=nodenoAccountDatabase(${phpQuote(storageRoot)});$user=null;if($fixture['userId']){$read=$db->prepare('SELECT * FROM users WHERE id=?');$read->execute([$fixture['userId']]);$user=$read->fetch();}$provider=$fixture['identity']['provider'];$flow=nodenoSocialCreateFlow($db,$provider,['clientId'=>'fixture.apps.googleusercontent.com','callback'=>'https://nodenohome.com/api/account/oauth/'.$provider.'/callback'],['sessionId'=>$fixture['sessionId'],'browser'=>$fixture['browser'],'intent'=>$fixture['intent'],'user'=>$user,'locale'=>'tr']);$data=nodenoSocialClaimFlow($db,$flow['state'],$provider,$fixture['browser']);nodenoSocialSaveVerified($db,$flow['state'],$data,$fixture['identity']);echo json_encode(['state'=>$flow['state']]);`;
    const fixture=spawnSync(php,['-r',program,JSON.stringify({identity,intent,browser,userId:account.data.user?.id||null,sessionId:jar.cookie.split('=')[1]})],{encoding:'utf8'});
    assert.equal(fixture.status,0,fixture.stderr||fixture.stdout);const state=JSON.parse(fixture.stdout).state;
    const response=await fetch(origin+'/api/account/oauth/complete?flow='+state,{redirect:'manual',headers:{Cookie:jar.cookie+'; __Secure-NODENOOAUTH='+browser}});
    assert.equal(response.status,303);
    const cookie=response.headers.getSetCookie().find(value=>value.startsWith('NODENOSESSID='));if(cookie)jar.cookie=cookie.split(';')[0];
    await request(jar,'/api/account');return response;
  }
  try {
    await start();
    const alice = client(), bob = client();
    const password = 'Alice-safe-password-2026';
    let addressId, originalCookie;
    await t.test('guest session, CSRF, Origin, body and cookie protections', async () => {
      const initial = await request(alice, '/api/account');
      assert.equal(initial.status, 200);
      assert.equal(initial.data.user, null);
      assert.match(alice.csrf, /^[a-f0-9]{64}$/);
      assert.deepEqual(initial.data.capabilities, {registration: true, passwordReset: false, checkout: false});
      assert.match(initial.headers.get('set-cookie'), /HttpOnly/i);
      assert.match(initial.headers.get('set-cookie'), /Secure/i);
      assert.match(initial.headers.get('set-cookie'), /SameSite=Lax/i);
      assert.match(initial.headers.get('cache-control'), /no-store/);
      const fixedCookie = 'NODENOSESSID=' + 'a'.repeat(26);
      const fixation = {cookie: fixedCookie, csrf: ''};
      assert.equal((await request(fixation, '/api/account')).status, 200);
      assert.notEqual(fixation.cookie, fixedCookie, 'Strict sessions must reject unissued client-selected IDs');
      const registration = {name: 'Alice Örnek', email: 'alice@example.test', password};
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', body: registration, headers: {'X-CSRF-Token': ''}})).status, 403);
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', body: registration, headers: {Origin: 'https://evil.invalid'}})).status, 403);
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', body: registration, headers: {Origin: ''}})).status, 403);
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', body: registration, headers: {'Content-Type': 'text/plain'}})).status, 415);
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', raw: '{'})).status, 400);
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', raw: '[]'})).status, 400);
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', raw: JSON.stringify({name: 'x'.repeat(40000)})})).status, 413);
      const chunked = await fetch(origin + '/api/account/register', {method: 'POST', headers: {
        Cookie: alice.cookie, Origin: origin, 'Content-Type': 'application/json', 'X-CSRF-Token': alice.csrf,
      }, body: new ReadableStream({start(controller) {controller.enqueue(Buffer.from(' '.repeat(33000))); controller.close();}}), duplex: 'half'});
      assert.equal(chunked.status, 413, 'Actual request bytes must be bounded without Content-Length');
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', body: {...registration, password: 'x'.repeat(73)}})).data.error, 'invalid_password');
      assert.equal((await request(alice, '/api/account/register', {method: 'POST', body: {...registration, password: 'ö'.repeat(37)}})).data.error, 'invalid_password');
      assert.equal((await request(alice, '/api/account/state')).status, 401);
      assert.equal((await request(alice, '/api/account?unsafe=1')).status, 503);
      await assert.rejects(stat(path.join(publicRoot, 'forbidden-account-data')), {code: 'ENOENT'});
    });
    await t.test('unconfigured social routes stay closed and preserve local account security', async () => {
      const guest=client();await request(guest,'/api/account');
      const social=await request(guest,'/api/account/social');assert.equal(social.status,200);
      assert.equal(social.data.providers.google.ready,false);assert.equal(social.data.providers.apple.ready,false);assert.equal(social.data.merge,null);
      for(const provider of ['google','apple']){
        const rejected=await request(guest,`/api/account/oauth/${provider}/start`,{method:'POST',body:{intent:'login'}});
        assert.equal(rejected.status,503);assert.equal(rejected.data.error,'social_not_configured');
      }
      const csrf=await request(guest,'/api/account/oauth/google/start',{method:'POST',body:{intent:'login'},headers:{'X-CSRF-Token':'wrong'}});assert.equal(csrf.status,403);
      assert.equal((await request(guest,'/api/account/social/merge',{method:'POST',body:{confirm:true}})).status,401);
      const callback=await fetch(origin+'/api/account/oauth/google/callback?state=invalid',{redirect:'manual',headers:{Cookie:guest.cookie}});
      assert.equal(callback.status,303);assert.match(callback.headers.get('location'),/^\/\?page=login&lang=tr&social=/);
      assert.equal(callback.headers.get('set-cookie'),null,'cross-site callback must not weaken or replace normal session');
      assert.equal((await request(guest,'/api/account')).data.user,null);
    });
    await t.test('password policy counts Unicode characters while retaining byte and NUL bounds', async () => {
      const account = client();
      await request(account, '/api/account');
      // Arabic Extended-A letters occupy three UTF-8 bytes per code point.
      const shortArabic = '\u08a0'.repeat(4), arabicPassword = '\u08a0'.repeat(12);
      const changedArabicPassword = '\u08a1'.repeat(12);
      assert.equal(Buffer.byteLength(shortArabic, 'utf8'), 12);
      assert.equal(Buffer.byteLength(arabicPassword, 'utf8'), 36);
      const registration = {name: 'Unicode Policy', email: 'unicode-policy@example.test'};
      for (const invalid of [shortArabic, 'x'.repeat(11), 'x'.repeat(73), 'Valid-password\0suffix']) {
        const rejected = await request(account, '/api/account/register', {method: 'POST', body: {...registration, password: invalid}});
        assert.equal(rejected.status, 422);
        assert.equal(rejected.data.error, 'invalid_password');
      }
      assert.equal((await request(account, '/api/account/register', {method: 'POST', body: {...registration, password: arabicPassword}})).status, 201);
      assert.equal((await request(account, '/api/account/password', {method: 'POST', body: {currentPassword: arabicPassword, password: shortArabic}})).status, 422);
      assert.equal((await request(account, '/api/account/password', {method: 'POST', body: {currentPassword: arabicPassword, password: changedArabicPassword}})).status, 200);
      assert.equal((await request(account, '/api/account/logout', {method: 'POST'})).status, 200);
      assert.equal((await request(account, '/api/account/login', {method: 'POST', body: {email: registration.email, password: changedArabicPassword}})).status, 200);
      assert.equal((await request(account, '/api/account', {method: 'DELETE', body: {password: changedArabicPassword}})).status, 200);
    });
    await t.test('registration and login rotate the session and preserve unique users', async () => {
      const guestCookie = alice.cookie, guestToken = alice.csrf;
      const registered = await request(alice, '/api/account/register', {method: 'POST', body: {name: 'Alice Örnek', email: 'Alice@Example.Test', password}});
      assert.equal(registered.status, 201);
      assert.equal(registered.data.user.email, 'alice@example.test');
      assert.equal(registered.data.user.emailVerified, false);
      assert.match(registered.data.user.id, /^[a-f0-9]{32}$/);
      assert.notEqual(alice.cookie, guestCookie);
      assert.notEqual(alice.csrf, guestToken);
      assert.equal((await request({cookie: guestCookie, csrf: guestToken}, '/api/account')).data.user, null);
      const duplicate = client();
      await request(duplicate, '/api/account');
      assert.equal((await request(duplicate, '/api/account/register', {method: 'POST', body: {name: 'Duplicate', email: 'ALICE@EXAMPLE.TEST', password}})).status, 409);
      await request(bob, '/api/account');
      assert.equal((await request(bob, '/api/account/register', {method: 'POST', body: {name: 'Bob Örnek', email: 'bob@example.test', password: 'Bob-safe-password-2026'}})).status, 201);
      originalCookie = alice.cookie;
      assert.equal((await request(alice, '/api/account/profile', {method: 'PATCH', body: {name: 'Alice Yeni'}})).data.user.name, 'Alice Yeni');
      const loggedOut = await request(alice, '/api/account/logout', {method: 'POST'});
      assert.equal(loggedOut.status, 200);
      assert.equal(loggedOut.data.user, null);
      assert.notEqual(alice.cookie, originalCookie);
      assert.equal((await request({cookie: originalCookie, csrf: ''}, '/api/account')).data.user, null);
      const beforeLogin = alice.cookie;
      assert.equal((await request(alice, '/api/account/login', {method: 'POST', body: {email: 'alice@example.test', password: 'wrong-password'}})).status, 401);
      assert.equal((await request(alice, '/api/account/login', {method: 'POST', body: {email: 'alice@example.test', password}})).status, 200);
      assert.notEqual(alice.cookie, beforeLogin);
    });
    const state = {cart: [{id: ids[0], quantity: 2}, {id: ids[1], quantity: 99}], favorites: [ids[0], ids[2]]};
    await t.test('cart and favorites validate canonical IDs and persist independently', async () => {
      assert.deepEqual((await request(alice, '/api/account/state')).data, {cart: [], favorites: []});
      assert.deepEqual((await request(alice, '/api/account/state', {method: 'PUT', body: state})).data, state);
      assert.deepEqual((await request(bob, '/api/account/state')).data, {cart: [], favorites: []});
      for (const invalid of [
        {cart: [{id: 'invented-id', quantity: 1}], favorites: []},
        {cart: [{id: ids[0], quantity: 100}], favorites: []},
        {cart: [{id: ids[0], quantity: 1.5}], favorites: []},
        {cart: [{id: ids[0], quantity: '2'}], favorites: []},
        {cart: ids.slice(0, 101).map(id => ({id, quantity: 1})), favorites: []},
        {cart: [], favorites: [...ids, ids[0]]},
      ]) assert.equal((await request(alice, '/api/account/state', {method: 'PUT', body: invalid})).status, 422);
      assert.deepEqual((await request(alice, '/api/account/state')).data, state);
    });
    const address = {label: 'Ev', name: 'Alice Yeni', phone: '+90 555 123 45 67', country: 'TR', city: 'İstanbul', district: 'Kadıköy', postalCode: '34710', line1: 'Örnek Sokak 10', line2: 'Daire 2', isDefault: true};
    await t.test('addresses enforce ownership, validation and exactly one default', async () => {
      const created = await request(alice, '/api/account/addresses', {method: 'POST', body: address});
      assert.equal(created.status, 201);
      addressId = created.data.address.id;
      assert.deepEqual(created.data.address, {...address, id: addressId});
      assert.deepEqual((await request(bob, '/api/account/addresses')).data, {addresses: []});
      assert.equal((await request(bob, `/api/account/addresses/${addressId}`, {method: 'PATCH', body: {line1: 'Hacked'}})).status, 404);
      assert.equal((await request(bob, `/api/account/addresses/${addressId}`, {method: 'DELETE'})).status, 404);
      assert.equal((await request(alice, '/api/account/addresses', {method: 'POST', body: {...address, phone: '<script>'}})).status, 422);
      const second = await request(alice, '/api/account/addresses', {method: 'POST', body: {...address, label: 'İş'}});
      assert.equal(second.status, 201);
      const addresses = (await request(alice, '/api/account/addresses')).data.addresses;
      assert.equal(addresses.filter(value => value.isDefault).length, 1);
      assert.equal(addresses.find(value => value.id === second.data.address.id).isDefault, true);
      assert.equal((await request(alice, `/api/account/addresses/${second.data.address.id}`, {method: 'DELETE'})).status, 200);
      const remaining = (await request(alice, '/api/account/addresses')).data.addresses;
      assert.equal(remaining[0].isDefault, true);
      assert.equal((await request(alice, `/api/account/addresses/${addressId}`, {method: 'PATCH', body: {line2: 'Daire 3'}})).data.address.line2, 'Daire 3');
    });
    await t.test('orders remain honest, email reset unavailable, and passwords revoke other sessions', async () => {
      assert.deepEqual((await request(alice, '/api/account/orders')).data, {orders: []});
      const order = await request(alice, '/api/account/orders', {method: 'POST', body: {items: state.cart, addressId}});
      assert.equal(order.status, 409);
      assert.equal(order.data.error, 'commerce_not_configured');
      assert.deepEqual((await request(alice, '/api/account/orders')).data, {orders: []});
      const reset = await request(alice, '/api/account/password-reset', {method: 'POST', body: {email: 'alice@example.test'}});
      assert.equal(reset.status, 503);
      assert.equal(reset.data.error, 'email_delivery_unavailable');
      const otherSession = client();
      await request(otherSession, '/api/account');
      assert.equal((await request(otherSession, '/api/account/login', {method: 'POST', body: {email: 'alice@example.test', password}})).status, 200);
      const beforeChange = alice.cookie, beforeToken = alice.csrf;
      assert.equal((await request(alice, '/api/account/password', {method: 'POST', body: {currentPassword: 'invalid-current', password: 'New-safe-password-2026'}})).status, 401);
      assert.equal((await request(alice, '/api/account/password', {method: 'POST', body: {currentPassword: password, password: 'New-safe-password-2026'}})).status, 200);
      assert.notEqual(alice.cookie, beforeChange);
      assert.notEqual(alice.csrf, beforeToken);
      assert.equal((await request(otherSession, '/api/account')).data.user, null);
      assert.equal((await request({cookie: beforeChange, csrf: beforeToken}, '/api/account')).data.user, null);
    });
    await t.test('SQLite state and session survive a PHP process restart', async () => {
      await stop();
      await start();
      assert.equal((await request(alice, '/api/account')).data.user.email, 'alice@example.test');
      assert.deepEqual((await request(alice, '/api/account/state')).data, state);
      assert.equal((await request(alice, '/api/account/addresses')).data.addresses[0].id, addressId);
      assert.deepEqual((await request(bob, '/api/account/state')).data, {cart: [], favorites: []});
      const inspection = spawnSync(php, ['-r', '$db=new PDO("sqlite:".$argv[1]); echo json_encode(["orders"=>(int)$db->query("SELECT COUNT(*) FROM orders")->fetchColumn(),"shipments"=>(int)$db->query("SELECT COUNT(*) FROM shipments")->fetchColumn(),"hashes"=>$db->query("SELECT password_hash FROM users")->fetchAll(PDO::FETCH_COLUMN),"rateKeys"=>$db->query("SELECT key_hash FROM rate_limits")->fetchAll(PDO::FETCH_COLUMN)]);', path.join(storageRoot, 'accounts.sqlite')], {encoding: 'utf8'});
      assert.equal(inspection.status, 0, inspection.stderr);
      const database = JSON.parse(inspection.stdout);
      assert.equal(database.orders, 0);
      assert.equal(database.shipments, 0);
      assert.ok(database.hashes.every(hash => hash.startsWith('$2') || hash.startsWith('$argon2')));
      assert.ok(database.rateKeys.every(key => /^[a-f0-9]{64}$/.test(key)));
    });
    await t.test('real order reads are scoped and order history prevents account deletion', async () => {
      const owner = client();
      await request(owner, '/api/account');
      const registered = await request(owner, '/api/account/register', {method: 'POST', body: {name: 'Order Fixture', email: 'order-owner@example.test', password: 'Order-safe-password-2026'}});
      assert.equal(registered.status, 201);
      const userId = registered.data.user.id;
      const fixture = spawnSync(php, ['-r', '$db=new PDO("sqlite:".$argv[1]); $db->setAttribute(PDO::ATTR_ERRMODE,PDO::ERRMODE_EXCEPTION); $s=$db->prepare("INSERT INTO orders(id,user_id,status,currency,total_minor,items_json,created_at) VALUES (?,?,?,?,?,?,?)"); $s->execute(["test-order",$argv[2],"shipped","TRY",15000,"[]",time()]); $s=$db->prepare("INSERT INTO shipments(id,order_id,carrier,tracking_number,tracking_url,status,updated_at) VALUES (?,?,?,?,?,?,?)"); $s->execute(["test-shipment","test-order","Test carrier","TRACK-1","https://tracking.example.test/TRACK-1","in_transit",time()]);', path.join(storageRoot, 'accounts.sqlite'), userId], {encoding: 'utf8'});
      assert.equal(fixture.status, 0, fixture.stderr);
      const orders = (await request(owner, '/api/account/orders')).data.orders;
      assert.equal(orders.length, 1);
      assert.equal(orders[0].id, 'test-order');
      assert.equal(orders[0].shipments[0].trackingNumber, 'TRACK-1');
      assert.deepEqual((await request(alice, '/api/account/orders')).data, {orders: []});
      assert.deepEqual((await request(bob, '/api/account/orders')).data, {orders: []});
      const removal = await request(owner, '/api/account', {method: 'DELETE', body: {password: 'Order-safe-password-2026'}});
      assert.equal(removal.status, 409);
      assert.equal(removal.data.error, 'account_has_orders');
      assert.equal((await request(owner, '/api/account')).data.user.id, userId);
    });
    await t.test('brute force attempts are durably limited', async () => {
      const attacker = client();
      await request(attacker, '/api/account');
      const statuses = [];
      for (let attempt = 0; attempt < 12; attempt++) statuses.push((await request(attacker, '/api/account/login', {method: 'POST', body: {email: 'bob@example.test', password: 'Invalid-safe-password'}})).status);
      assert.ok(statuses.includes(401));
      assert.equal(statuses.at(-1), 429);
      await stop();
      await start();
      const retry = await request(attacker, '/api/account/login', {method: 'POST', body: {email: 'bob@example.test', password: 'Invalid-safe-password'}});
      assert.equal(retry.status, 429);
      assert.ok(Number(retry.headers.get('retry-after')) > 0);
    });
    await t.test('confirmed account deletion cascades own data and preserves other users', async () => {
      const oldCookie = alice.cookie, oldToken = alice.csrf;
      const aliceId = (await request(alice, '/api/account')).data.user.id;
      const bobId = (await request(bob, '/api/account')).data.user.id;
      const wrong = await request(alice, '/api/account', {method: 'DELETE', body: {password: 'Wrong-current-password'}});
      assert.equal(wrong.status, 401);
      assert.equal((await request(alice, '/api/account')).data.user.id, aliceId);
      const deleted = await request(alice, '/api/account', {method: 'DELETE', body: {password: 'New-safe-password-2026'}});
      assert.equal(deleted.status, 200);
      assert.equal(deleted.data.user, null);
      assert.notEqual(alice.cookie, oldCookie);
      assert.notEqual(alice.csrf, oldToken);
      assert.equal((await request(alice, '/api/account/state')).status, 401);
      assert.equal((await request({cookie: oldCookie, csrf: oldToken}, '/api/account')).data.user, null);
      assert.equal((await request(bob, '/api/account')).data.user.id, bobId);
      assert.deepEqual((await request(bob, '/api/account/state')).data, {cart: [], favorites: []});
      const inspection = spawnSync(php, ['-r', '$db=new PDO("sqlite:".$argv[1]); $counts=[]; foreach (["users"=>"id","addresses"=>"user_id","account_state"=>"user_id"] as $table=>$column) {$s=$db->prepare("SELECT COUNT(*) FROM ".$table." WHERE ".$column."=?");$s->execute([$argv[2]]);$counts[$table]=(int)$s->fetchColumn();} echo json_encode($counts);', path.join(storageRoot, 'accounts.sqlite'), aliceId], {encoding: 'utf8'});
      assert.equal(inspection.status, 0, inspection.stderr);
      assert.deepEqual(JSON.parse(inspection.stdout), {users: 0, addresses: 0, account_state: 0});
    });
    await t.test('verified social completion rotates the real session and supports a safe password lifecycle',async()=>{
      const owner=client();await request(owner,'/api/account');const previous=owner.cookie;
      const identity={provider:'google',subject:'test-social-owner',email:'social-owner@example.test',emailVerified:true,name:'Social Owner'};
      const completed=await completeVerifiedFixture(owner,identity);assert.match(completed.headers.get('location'),/^\/\?page=account&lang=tr$/);assert.notEqual(owner.cookie,previous);
      let user=(await request(owner,'/api/account')).data.user;assert.equal(user.emailVerified,true);assert.equal(user.hasPassword,false);
      const last=await request(owner,'/api/account/social/unlink',{method:'POST',body:{provider:'google'}});assert.equal(last.status,409);assert.equal(last.data.error,'social_last_login_method');
      const password='Social-owner-new-password-2026';const created=await request(owner,'/api/account/password',{method:'POST',body:{password}});assert.equal(created.status,200);assert.equal(created.data.user.hasPassword,true);
      const unlink=await request(owner,'/api/account/social/unlink',{method:'POST',body:{provider:'google',currentPassword:password}});assert.equal(unlink.status,200);
      assert.equal((await request(owner,'/api/account/social')).data.providers.google.linked,false);
      await request(owner,'/api/account/logout',{method:'POST'});assert.equal((await request(owner,'/api/account/login',{method:'POST',body:{email:identity.email,password}})).status,200);
    });
    await t.test('two proven accounts merge only after an explicit CSRF-protected confirmation',async()=>{
      const target=client(),source=client();await request(target,'/api/account');await request(source,'/api/account');
      const left={provider:'google',subject:'merge-target',email:'merge-target@example.test',emailVerified:true,name:'Merge Target'};
      const right={provider:'apple',subject:'merge-source',email:'merge-source@privaterelay.appleid.com',emailVerified:true,name:'Merge Source'};
      await completeVerifiedFixture(target,left);await completeVerifiedFixture(source,right);
      const targetId=(await request(target,'/api/account')).data.user.id;
      await request(target,'/api/account/state',{method:'PUT',body:{cart:[{id:ids[0],quantity:2}],favorites:[ids[0]]}});
      await request(source,'/api/account/state',{method:'PUT',body:{cart:[{id:ids[1],quantity:3}],favorites:[ids[1]]}});
      const proposed=await completeVerifiedFixture(target,right,'link');assert.match(proposed.headers.get('location'),/social=merge_ready/);
      assert.equal((await request(target,'/api/account')).data.user.id,targetId);
      const status=(await request(target,'/api/account/social')).data;assert.equal(status.merge.provider,'apple');
      assert.equal((await request(target,'/api/account/social/merge',{method:'POST',body:{confirm:true,confirmation:'incorrect'}})).status,409);
      const merged=await request(target,'/api/account/social/merge',{method:'POST',body:{confirm:true,confirmation:status.merge.confirmation}});assert.equal(merged.status,200);assert.equal(merged.data.user.id,targetId);
      assert.deepEqual((await request(target,'/api/account/state')).data,{cart:[{id:ids[0],quantity:2},{id:ids[1],quantity:3}],favorites:[ids[0],ids[1]]});
      assert.equal((await request(source,'/api/account')).data.user,null);
      assert.equal((await request(target,'/api/account/social')).data.providers.apple.linked,true);
    });
    assert.doesNotMatch(output, /(?:PHP (?:Warning|Deprecated|Fatal)|Alice-safe-password|New-safe-password)/);
  } finally {
    await stop();
    if (path.dirname(temporary) !== os.tmpdir() || !path.basename(temporary).startsWith('nodeno-account-')) throw new Error('Unsafe account test cleanup');
    await rm(temporary, {recursive: true, force: true});
  }
});
