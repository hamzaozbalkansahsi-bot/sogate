"""Pixel equality alone does not transfer a different object's visual disposition."""
def same_review_target(previous_box,current_box):
 return (isinstance(previous_box,(list,tuple)) and isinstance(current_box,(list,tuple))
         and len(previous_box)==len(current_box)==4 and tuple(previous_box)==tuple(current_box))
