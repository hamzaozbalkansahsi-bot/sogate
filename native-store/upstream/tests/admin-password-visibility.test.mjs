import test from 'node:test';
import assert from 'node:assert/strict';
import {togglePasswordVisibility} from '../web/admin-password-visibility.js';
test('show/hide preserves typed password, caret and native form constraints',()=>{
 const input={type:'password',value:'Nödëno-Deneme-2026',selectionStart:4,selectionEnd:8,required:true,minLength:14,autocomplete:'new-password',setSelectionRange(start,end){this.selectionStart=start;this.selectionEnd=end;}},button={attrs:{},setAttribute(k,v){this.attrs[k]=v;}};
 togglePasswordVisibility(input,button);assert.equal(input.type,'text');assert.equal(button.attrs['aria-pressed'],'true');assert.equal(button.attrs['aria-label'],'Parolayı göster');assert.equal(input.value,'Nödëno-Deneme-2026');assert.deepEqual([input.selectionStart,input.selectionEnd],[4,8]);
 togglePasswordVisibility(input,button);assert.equal(input.type,'password');assert.equal(button.attrs['aria-pressed'],'false');assert.equal(button.attrs['aria-label'],'Parolayı göster');assert.equal(input.required,true);assert.equal(input.minLength,14);assert.equal(input.autocomplete,'new-password');assert.doesNotMatch(button.innerHTML,/Nödëno|Deneme/);
});
