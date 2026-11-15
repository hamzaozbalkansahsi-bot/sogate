"""Scoped public assets with readback, lost-ack handling and guarded rollback."""
from contextlib import contextmanager

class ConcurrentPointerError(RuntimeError):pass

@contextmanager
def public_assets_transaction(previous,proposed,*,read,write):
 if set(previous)!=set(proposed):raise ValueError('public change set differs')
 if any(read(name)!=body for name,body in previous.items()):raise RuntimeError('concurrent public edit before switch')
 touched=[]
 try:
  for name,body in proposed.items():
   touched.append(name)
   try:write(name,body)
   except Exception:
    if read(name)!=body:raise
   if read(name)!=body:raise RuntimeError('public upload readback differs')
  yield
 except ConcurrentPointerError:
  raise
 except BaseException as cause:
  conflict=False
  for name in reversed(touched):
   old=previous[name];current=read(name)
   if current==old:continue
   if current!=proposed[name]:conflict=True;continue
   # New helper modules contain no data and remain unreferenced after HTML/JS
   # rollback; never delete files as part of this publication operation.
   if old is None:continue
   try:write(name,old)
   except Exception:
    if read(name)!=old:raise
   if read(name)!=old:raise RuntimeError('public rollback readback differs')from cause
  if conflict:raise RuntimeError('concurrent public edit preserved during rollback')from cause
  raise

def switch_with_public_assets(old_pointer,new_pointer,previous,proposed,*,read_pointer,write_pointer,read_asset,write_asset,health,is_new,is_old):
 """Verify health only when a complete public/private pair is present.

 Both releases fingerprint public assets. Do not call the private-only pointer
 helper between their updates; it would reject an intentionally incomplete pair.
 """
 if read_pointer()!=old_pointer:raise ConcurrentPointerError('concurrent runtime pointer before public update')
 try:
  with public_assets_transaction(previous,proposed,read=read_asset,write=write_asset):
   try:
    if read_pointer()!=old_pointer:raise ConcurrentPointerError('concurrent runtime pointer preserved')
    try:write_pointer(new_pointer)
    except Exception:
     if read_pointer()!=new_pointer:raise
    if read_pointer()!=new_pointer:raise ConcurrentPointerError('concurrent runtime pointer preserved')
    accepted=health()
    if not is_new(accepted):raise RuntimeError('new release health failed')
    return accepted
   except BaseException:
    if read_pointer()not in [old_pointer,new_pointer]:raise ConcurrentPointerError('concurrent runtime pointer preserved')from None
    raise
 except ConcurrentPointerError:raise
 except BaseException as cause:
  current=read_pointer()
  if current not in [old_pointer,new_pointer]:raise ConcurrentPointerError('concurrent runtime pointer preserved during rollback')from cause
  if current==new_pointer:
   try:write_pointer(old_pointer)
   except Exception:
    if read_pointer()!=old_pointer:raise RuntimeError('old runtime pointer restoration failed')from cause
  if read_pointer()!=old_pointer or not is_old(health()):raise RuntimeError('old complete release verification failed; failed release was not reactivated')from cause
  raise
