// A local checkout draft, not an order or a payment request.
export function validateGuestCheckout(data={}){
 const errors={},values={};
 function text(key,{required=true,min=1,max=160,multiline=false}={}){
  const value=typeof data[key]==='string'?data[key].trim().replace(/\r\n?/g,'\n'):'';
  if(required&&value.length<min)errors[key]='guestRequired';
  else if(value.length>max)errors[key]='guestTooLong';
  else if((multiline?/[<>\u0000-\u0008\u000b-\u001f\u007f]/u:/[<>\u0000-\u001f\u007f]/u).test(value))errors[key]='guestInvalid';
  return value;
 }
 values.name=text('name',{min:2,max:120});values.email=text('email',{max:254});values.phone=text('phone',{max:30});
 values.phone=values.phone.replace(/[\u0660-\u0669\u06f0-\u06f9]/gu,c=>String(c.charCodeAt(0)-(c.charCodeAt(0)>=0x06f0?0x06f0:0x0660)));
 if(values.email&&!/^[^\s<>"'@]+@[^\s<>"'@]+\.[^\s<>"'@]+$/u.test(values.email))errors.email='guestInvalidEmail';
 if(values.phone&&(!/^[+\d() .-]+$/u.test(values.phone)||values.phone.replace(/\D/g,'').length<7||values.phone.replace(/\D/g,'').length>15))errors.phone='guestInvalidPhone';
 function address(prefix='',name=values.name){return{name:prefix?text(prefix+'name',{min:2,max:120}):name,country:text(prefix+'country',{min:2,max:80}),city:text(prefix+'city',{min:2,max:100}),district:text(prefix+'district',{required:false,max:100}),postalCode:text(prefix+'postalCode',{required:false,max:20}),line1:text(prefix+'line1',{min:5,max:400,multiline:true}),line2:text(prefix+'line2',{required:false,max:250,multiline:true})};}
 values.delivery=address();values.sameBilling=data.sameBilling!==false;values.billing=values.sameBilling?{...values.delivery}:address('billing_');
 return{valid:!Object.keys(errors).length,values,errors};
}
