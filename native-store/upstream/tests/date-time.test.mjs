import test from 'node:test';
import assert from 'node:assert/strict';
import {formatDate,formatDateTime,formatTime,dateTimeSettings,dateTimeInput,parseDateTimeInput} from '../web/date-time.js';
test('Türkiye uses slash-separated Gregorian dates and Istanbul 24-hour time across UTC midnight',()=>{
 assert.equal(formatDate('2026-11-12',{country:'TR'}),'12/11/2026');
 assert.equal(formatDateTime('2026-11-12T21:05:00Z',{country:'TR'}),'13/11/2026 00:05');
 assert.equal(formatTime('2026-11-12T19:05:00Z',{country:'TR'}),'22:05');
});
test('country choice controls formatting independently of interface language',()=>{
 assert.equal(formatDate('2026-11-12',{country:'US',language:'tr'}),'11/12/2026');
 assert.equal(formatDate('2026-11-12',{country:'GB',language:'en'}),'12/11/2026');
 assert.equal(formatDate('2026-11-12',{country:'DE',language:'tr'}),'12.11.2026');
 assert.equal(dateTimeSettings('TR').timeZone,'Europe/Istanbul');assert.equal(dateTimeSettings('GB').timeZone,'Europe/London');
});
test('civil dates do not change day when the chosen country is across the date line',()=>{
 assert.equal(formatDate('2026-11-12',{country:'US',timeZone:'America/Los_Angeles'}),'11/12/2026');
 assert.ok(formatDate('2026-11-12',{country:'NZ',timeZone:'Pacific/Auckland'}).includes('12'));
 assert.equal(formatDate('invalid',{country:'TR'}),'');
 assert.equal(formatDate('2026-02-30',{country:'TR'}),'');
});
test('date-time form values round-trip through the country zone rather than device zone',()=>{
 assert.equal(dateTimeInput('2026-11-12T21:05:00Z',{country:'TR'}),'2026-11-13T00:05');
 assert.equal(parseDateTimeInput('2026-11-13T00:05',{country:'TR'}).toISOString(),'2026-11-12T21:05:00.000Z');
 assert.throws(()=>parseDateTimeInput('2026-03-29T01:30',{country:'GB'}),/nonexistent_local_time/);
});
