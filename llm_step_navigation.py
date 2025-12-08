
def build_step_context(current_step: int, total_steps: int) -> str:
    """Generate step tracking context for the LLM"""
    if current_step == 0:
        status = "Recipe not started yet."
        next_action = "When user says 'start' or 'next', provide Step 1."
    elif current_step > total_steps:
        status = f"Recipe completed! All {total_steps} steps done."
        next_action = "Congratulate the user and offer to answer questions or review steps."
    else:
        status = f"Currently at Step {current_step} of {total_steps} ({int((current_step / total_steps) * 100)}% complete)"
        next_action = f"User is working on Step {current_step}."
    
    return f"""
═══════════════════════════════════════
STEP TRACKER STATUS:
Current Step: {current_step}
Total Steps: {total_steps}
Status: {status}
{next_action}
═══════════════════════════════════════
"""


def build_navigation_instruction(user_input: str, current_step: int, total_steps: int) -> str:
    """Generate specific instructions based on detected navigation"""
    user_lower = user_input.lower()
    
    # Start from beginning
    if any(word in user_lower for word in ["start", "begin", "first step"]):
        return f"\n🎯 USER IS STARTING THE RECIPE. Return Step 1 clearly with its number and instructions.\n"
    
    # Next step
    if any(word in user_lower for word in ["next", "continue", "what's next", "done"]):
        if current_step >= total_steps:
            return f"\n🎯 USER REQUESTED NEXT STEP BUT RECIPE IS COMPLETE. Congratulate them!\n"
        return f"\n🎯 USER REQUESTED NEXT STEP. Return Step {current_step} clearly with its number and instructions. Do not skip ahead.\n"
    
    # Previous step
    if any(word in user_lower for word in ["previous", "go back", "repeat", "last step"]):
        return f"\n🎯 USER WANTS TO GO BACK. Return Step {current_step} clearly with its number and instructions.\n"
    
    # Jump to specific step
    import re
    step_match = re.search(r'step (\d+)', user_lower)
    if step_match:
        step_num = int(step_match.group(1))
        if step_num <= total_steps:
            return f"\n🎯 USER REQUESTED SPECIFIC STEP. Return Step {step_num} clearly with its number and instructions.\n"
    
    # General question about current context
    if current_step > 0 and current_step <= total_steps:
        return f"\n💬 USER HAS A QUESTION. They are currently on Step {current_step}. Answer their question based on the recipe context.\n"
    
    return "\n💬 USER HAS A QUESTION. Answer based on the recipe context.\n"


def detect_step_navigation(user_input: str, current_step: int, total_steps: int) -> int:
    """Detect if user is navigating steps and update current_step accordingly"""
    user_lower = user_input.lower()
    
    # Start from beginning
    if any(word in user_lower for word in ["start", "begin", "first step"]):
        return 1
    
    # Next step
    if any(word in user_lower for word in ["next", "continue", "what's next", "done"]):
        return min(current_step + 1, total_steps + 1)
    
    # Previous step
    if any(word in user_lower for word in ["previous", "go back", "repeat", "last step"]):
        return max(1, current_step - 1)
    
    # Jump to specific step
    import re
    step_match = re.search(r'step (\d+)', user_lower)
    if step_match:
        step_num = int(step_match.group(1))
        return min(max(1, step_num), total_steps + 1)
    
    # No navigation detected
    return current_step
