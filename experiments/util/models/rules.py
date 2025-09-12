MUTANT_VALIDATOR_LEVEL_RULES = {
    'BASE': '\n- Your response must contain only the full version of modified class code with no explanations, comments, or additional text added by you.\n- The original comments present in the code should remain intact.\n- The mutation must be confined to a single method.\n- Do not create new methods.',
    'RELAXED': '\n- Do not introduce calls to `System.*` or `Random.*`.\n- Do not create mutants that involve only formatting or comment changes.\n- Do not add, remove, or modify comments.',
    'MODERATE': '\n- Do not introduce additional logical operators (`&&`, `||`).\n- Do not use ternary operators.\n- Do not introduce new control structures (`switch`, `if`, `for`, etc.), but modifications within existing structures are allowed.',
    'STRICT': '\n- No reflection.\n- No bitwise operators (bitshifts and logical).\n- Do not change method signatures (parameters or return types).'
}

TEST_RULES = {
    'BASE': '\n- Use the given test template (boilerplate is explicitly provided).\n- Include only one assertion.\n- Do not use loops, conditionals, calls to System.*, or define new methods.\n- The assertion may verify expected vs. actual values or check for exceptions, depending on the bug introduced.'
}
