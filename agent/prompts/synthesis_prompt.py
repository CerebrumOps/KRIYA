# ==============================================================================
# KRIYA - Final Synthesis Directive Prompt
# ==============================================================================
# Injected when tools have finished executing to compel the model to write its
# final comprehensive engineering report.
# ==============================================================================

FINAL_SYNTHESIS_PROMPT = (
    "Execution phase is complete. All necessary tool actions, database queries, and calculations have concluded. "
    "Provide your complete, comprehensive final engineering report for the plant operator based on the tool findings and deliverables above. "
    "Present key findings, numerical calculations, compliance verifications, and operational recommendations. "
    "Do not request further tool execution; deliver the full final report now."
)
