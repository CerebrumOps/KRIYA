# ==============================================================================
# KRIYA - Final Synthesis Directive Prompt
# ==============================================================================
# Injected when tools have finished executing to compel the model to write its
# final comprehensive engineering report.
# ==============================================================================

FINAL_SYNTHESIS_PROMPT = (
    "Execution phase is complete. All necessary tool actions, database queries, and calculations have concluded. "
    "Provide your complete, comprehensive final engineering response for the plant operator based on the tool outputs above. "
    "If any tool returned `ACCESS_DENIED` due to RBAC clearance restrictions, strictly report the access denial without fabricating data or deliverables. "
    "ONLY if a document generator tool (`generate_word_document`, `generate_excel_spreadsheet`, `generate_powerpoint_deck`) or `execute_terminal_command` "
    "actually wrote a physical file to disk during this turn, conclude your response with: `[Deliverable Created]: <Document Title> saved to '<filename>'`. "
    "If no file was created on disk in this turn, DO NOT include any `[Deliverable Created]` line. "
    "Do not request further tool execution; deliver the full final response now."
)
