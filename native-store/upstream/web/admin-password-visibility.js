export function passwordVisibilityIcon(shown=false){
 const shape=shown?'<path d="m3 3 18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 4.2A10.7 10.7 0 0 1 12 4c5.5 0 9 8 9 8a17.4 17.4 0 0 1-3.1 4.1M6.2 6.2A19 19 0 0 0 3 12s3.5 8 9 8a10.2 10.2 0 0 0 5.8-2.2"/>':'<path d="M3 12s3.5-8 9-8 9 8 9 8-3.5 8-9 8-9-8-9-8Z"/><circle cx="12" cy="12" r="3"/>';
 return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${shape}</svg>`;
}
export function togglePasswordVisibility(input,button){
 const show=input.type==='password',start=input.selectionStart,end=input.selectionEnd;
 input.type=show?'text':'password';
 if(Number.isInteger(start)&&Number.isInteger(end))input.setSelectionRange(start,end);
 button.setAttribute('aria-pressed',String(show));button.setAttribute('aria-label','Parolayı göster');button.innerHTML=passwordVisibilityIcon(show);
}
