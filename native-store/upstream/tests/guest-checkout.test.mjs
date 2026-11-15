import test from 'node:test';
import assert from 'node:assert/strict';
import {validateGuestCheckout} from '../web/guest-checkout.js';
const details={name:'Deniz Örnek',email:'deniz@example.test',phone:'+90 532 123 45 67',country:'Türkiye',city:'İstanbul',district:'Kadıköy',postalCode:'34710',line1:'Örnek Mahallesi Deneme Sokak 12',line2:'Daire 3',sameBilling:true};
test('a guest can prepare contact, delivery and billing without a user ID or password',()=>{
 const result=validateGuestCheckout(details);assert.equal(result.valid,true);assert.equal(result.values.email,details.email);assert.deepEqual(result.values.billing,result.values.delivery);assert.equal(result.values.name,details.name);
 assert.ok(!('password' in result.values));assert.ok(!('userId' in result.values));
});
test('international names, phone numbers and alphanumeric postcodes remain supported',()=>{
 const result=validateGuestCheckout({...details,name:'Алексей أحمد',phone:'+44 (20) 7123-4567',country:'United Kingdom',city:'London',district:'',postalCode:'SW1A 1AA'});assert.equal(result.valid,true);assert.equal(result.values.delivery.postalCode,'SW1A 1AA');
 const arabic=validateGuestCheckout({...details,phone:'+٩٠ ٥٣٢ ١٢٣ ٤٥ ٦٧'});assert.equal(arabic.valid,true);assert.equal(arabic.values.phone,'+90 532 123 45 67');
});
test('invalid and oversized fields are rejected without echoing unsafe values as HTML',()=>{
 for(const change of [{name:''},{email:'wrong'},{phone:'abc123'},{line1:'x'},{name:'<img src=x onerror=alert(1)>'},{line1:'a'.repeat(401)},{city:'Paris\u0000'}]){const result=validateGuestCheckout({...details,...change});assert.equal(result.valid,false);assert.ok(Object.keys(result.errors).length);}
});
test('separate billing is validated and inactive billing fields do not block same-address checkout',()=>{
 const invalid=validateGuestCheckout({...details,sameBilling:false});assert.equal(invalid.valid,false);assert.ok(invalid.errors.billing_name);
 const result=validateGuestCheckout({...details,sameBilling:false,billing_name:'Fatura Alıcısı',billing_country:'Türkiye',billing_city:'Ankara',billing_line1:'Başka Adres Sokak 10',billing_postalCode:'06000'});assert.equal(result.valid,true);assert.equal(result.values.billing.city,'Ankara');assert.equal(result.values.delivery.city,'İstanbul');
 assert.equal(validateGuestCheckout({...details,billing_name:'<script>'}).valid,true);
});
test('normalization does not mutate caller data or accept injected identity, price or payment fields',()=>{
 const input={...details,name:'  Deniz Örnek  ',password:'secret',userId:'other-user',total:1,paid:true};const before=structuredClone(input),result=validateGuestCheckout(input);assert.deepEqual(input,before);assert.equal(result.values.name,'Deniz Örnek');for(const key of ['password','userId','total','paid'])assert.ok(!(key in result.values));
});
