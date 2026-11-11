"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/ui.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
// Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
// Dosya: src/components/ui.tsx | Açıklama: Klavye odağını koruyan erişilebilir dialog ve ortak arayüz bileşenleri.
import {useEffect,useRef,useId,type ReactNode,type KeyboardEvent} from "react";
import {X,ArrowRight,LoaderCircle} from "lucide-react";
import Link from "./localized-link";
import {useStore} from "./store-context";
export function Modal({open,onClose,title,children,closable=true}:{open:boolean;onClose:()=>void;title:string;children:ReactNode;closable?:boolean}) {
 const ref=useRef<HTMLDialogElement>(null),titleId=useId();
 useEffect(()=>{const dialog=ref.current;if(!dialog)return;if(open){const prior=document.activeElement;const previousOverflow=document.body.style.overflow;dialog.showModal();document.body.style.overflow="hidden";return()=>{dialog.close();document.body.style.overflow=previousOverflow;if(prior instanceof HTMLElement&&prior.isConnected)prior.focus();};}dialog.close();},[open]);
 function keepFocus(event:KeyboardEvent<HTMLDialogElement>){
  if(event.key!=="Tab")return;
  const dialog=event.currentTarget;
  const focusable=Array.from(dialog.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]):not([type="hidden"]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(element=>element.getClientRects().length>0&&element.getAttribute("aria-hidden")!=="true"&&!element.closest("[inert]"));
  const first=focusable[0],last=focusable.at(-1),active=document.activeElement;
  if(!first||!last){event.preventDefault();dialog.focus();return;}
  event.preventDefault();
  const current=focusable.indexOf(active as HTMLElement);
  const next=event.shiftKey?(current<=0?focusable.length-1:current-1):(current<0||current===focusable.length-1?0:current+1);
  focusable[next].focus();
 }
 return <dialog ref={ref} className="modal" tabIndex={-1} aria-labelledby={titleId} onKeyDown={keepFocus} onCancel={e=>{e.preventDefault();if(closable)onClose();}} onClick={e=>{if(e.target===e.currentTarget&&closable)onClose();}}>{open&&<div className="modal-inner"><div className="modal-title"><h2 id={titleId}>{title}</h2>{closable&&<button className="icon-button" type="button" onClick={onClose} aria-label="Kapat / Close"><X size={22}/></button>}</div>{children}</div>}</dialog>;
}
export function Status({error,message}:{error?:string;message?:string}){return <div className={error?"feedback error":"feedback"} role={error?"alert":"status"} aria-live="polite">{error||message||""}</div>;}
export function Busy(){const {t}=useStore();return <div className="busy" role="status"><LoaderCircle size={22} className="spin"/>{t("loading")}</div>;}
export function Empty({title,text,href,label}:{title:string;text?:string;href?:string;label?:string}){return <div className="empty"><div className="empty-arch" aria-hidden="true">S</div><h2>{title}</h2>{text&&<p>{text}</p>}{href&&<Link className="button" href={href}>{label}<ArrowRight size={17}/></Link>}</div>;}
export function PageHeading({eyebrow,title,description}:{eyebrow?:string;title:string;description?:string}){return <div className="page-heading">{eyebrow&&<p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description&&<p>{description}</p>}</div>;}
