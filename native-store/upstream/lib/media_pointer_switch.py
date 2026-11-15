"""Guarded pointer switch; callers must hold the shared deployment lease."""
def switch_pointer(old_pointer,new_pointer,plan,*,read,write,health,error=RuntimeError):
 try:write(new_pointer)
 except Exception:
  actual=read()
  if actual==old_pointer:raise error('media_pointer_write_failed_previous_retained')from None
  if actual!=new_pointer:raise error('concurrent_runtime_pointer_preserved')from None
 if read()!=new_pointer:raise error('concurrent_runtime_pointer_preserved')
 try:
  result=health()
  if not(result.get('status')=='ok'and result.get('releaseHash')==plan['releaseHash']and result.get('mediaVersion')==plan['mediaVersion']and result.get('checkoutEnabled')is False and result.get('mediaReady')is True):raise error('media_new_health_failed')
  return result
 except Exception:
  if read()!=new_pointer:raise error('concurrent_runtime_pointer_preserved')from None
  try:write(old_pointer)
  except Exception:
   if read()!=old_pointer:raise error('media_rollback_verification_failed')from None
  if read()!=old_pointer or health().get('releaseHash')!=plan['baseReleaseHash']:raise error('media_rollback_verification_failed')from None
  raise error('media_new_health_failed_previous_restored')from None
