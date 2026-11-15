import test from 'node:test';
import assert from 'node:assert/strict';
import * as app from '../web/app.js';

test('published contact details produce usable email telephone and social links',()=>{
 const links=app.contactLinks?.({contactEmail:'info@nodenohome.com',contactPhone:'0850 305 84 78',contactPhoneUri:'tel:+908503058478',domain:'nodenohome.com',website:'https://nodenohome.com',socials:[{id:'instagram',label:'Instagram',url:'https://www.instagram.com/nodenohome/'}]});
 assert.deepEqual(links,[
  {kind:'email',label:'info@nodenohome.com',href:'mailto:info@nodenohome.com'},
  {kind:'phone',label:'0850 305 84 78',href:'tel:+908503058478'},
  {kind:'website',label:'nodenohome.com',href:'https://nodenohome.com/'},
  {kind:'social',label:'Instagram',href:'https://www.instagram.com/nodenohome/'}
 ]);
});
test('contact links reject executable URLs and unsafe or incomplete contact values',()=>{
 const links=app.contactLinks?.({contactEmail:'info@nodenohome.com"><script>',contactPhone:'a number',contactPhoneUri:'javascript:alert(1)',website:'javascript:alert(1)',domain:'nodenohome.com',socials:[{label:'bad',url:'javascript:alert(1)'},{label:'bad',url:'https://name:secret@example.com/'},{label:'valid',url:'https://www.pinterest.com/nodenohome/'}]});
 assert.deepEqual(links,[{kind:'social',label:'valid',href:'https://www.pinterest.com/nodenohome/'}]);
});
