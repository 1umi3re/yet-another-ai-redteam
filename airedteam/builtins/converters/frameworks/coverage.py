from __future__ import annotations

PYRIT_TEXT_COMPATIBLE = {
    "ansi_escape",
    "add_image_text",
    "add_image_to_video",
    "add_text_image",
    "ascii_art",
    "ascii_smuggler",
    "ask_to_decode",
    "atbash",
    "audio_echo",
    "audio_frequency",
    "audio_speed",
    "audio_volume",
    "audio_white_noise",
    "azure_speech_audio_to_text",
    "azure_speech_text_to_audio",
    "base2048",
    "base64",
    "bin_ascii",
    "binary",
    "braille",
    "caesar",
    "camel_case",
    "char_swap",
    "character_space",
    "code_chameleon",
    "colloquial_wordswap",
    "control_chars_injection",
    "denylist",
    "diacritic",
    "ecoji",
    "emoji_substitution",
    "emoji_byte",
    "emoji_smuggling",
    "first_letter",
    "flip_text",
    "hex",
    "human_in_the_loop",
    "image_color_saturation",
    "image_compression",
    "image_resizing",
    "image_rotation",
    "insert_punctuation",
    "json_string",
    "leetspeak",
    "llm_generic",
    "llm_malicious_question",
    "llm_persuasion",
    "llm_random_translation",
    "llm_scientific_translation",
    "llm_tone",
    "llm_toxic_sentence",
    "llm_variation",
    "lowercase",
    "math_obfuscation",
    "markdown_wrapper",
    "math_prompt",
    "math_unicode",
    "morse",
    "nato",
    "negation_trap",
    "noise",
    "prefix",
    "pdf",
    "prompt_injection",
    "qr_code",
    "random_case",
    "repeat_token",
    "rot13",
    "search_replace",
    "selective_text",
    "skeleton_key",
    "sneaky_bits_smuggler",
    "string_join",
    "suffix_append",
    "superscript",
    "template_jailbreak",
    "template_segment",
    "tense",
    "translation_llm",
    "transparency_attack",
    "homoglyph",
    "unicode_escape",
    "unicode_obfuscation",
    "unicode_replacement",
    "unicode_substitution",
    "unicode_tag_obfuscation",
    "url_encode",
    "variation_selector_smuggler",
    "word_scramble",
    "word_doc",
    "zalgo",
    "zero_width",
}

GARAK_BUFF_COMPATIBLE = {
    "base64",
    "char_code",
    "low_resource_language",
    "lowercase",
    "translation_llm",
    "llm_variation",
    "paraphrase_fast",
    "paraphrase_pegasus",
}

GARAK_CURRENT_BUFF_INVENTORY = {
    "base64",
    "char_code",
    "low_resource_language",
    "lowercase",
    "paraphrase_fast",
    "paraphrase_pegasus",
}

AEGISRT_TEXT_COMPATIBLE = {
    "base64",
    "rot13",
    "hex",
    "caesar",
    "url_encode",
    "morse",
    "homoglyph",
    "zero_width",
    "whitespace",
    "case_swap",
    "flip_text",
    "character_space",
    "leetspeak",
    "pig_latin",
    "translation_llm",
    "llm_variation",
    "word_substitution",
    "acronym",
    "sandwich",
    "suffix",
    "few_shot",
    "role_prefix",
    "instruction_tag",
    "markdown_wrapper",
    "payload_split",
    "fictional",
    "research",
}

AEGISRT_CURRENT_CONVERTER_INVENTORY = {
    "base64",
    "rot13",
    "hex",
    "caesar",
    "url_encode",
    "morse",
    "homoglyph",
    "zero_width",
    "whitespace",
    "case_swap",
    "flip_text",
    "character_space",
    "leetspeak",
    "pig_latin",
    "translation_llm",
    "llm_variation",
    "word_substitution",
    "acronym",
    "sandwich",
    "suffix",
    "few_shot",
    "role_prefix",
    "instruction_tag",
    "markdown_wrapper",
    "payload_split",
    "fictional",
    "research",
}

EASYJAILBREAK_CURRENT_RULE_MUTATOR_INVENTORY = {
    "artificial",
    "ascii_expert",
    "auto_obfuscation",
    "auto_payload_splitting",
    "base64",
    "base64_input_only",
    "base64_raw",
    "binary_tree",
    "caser_expert",
    "combination_1",
    "combination_2",
    "combination_3",
    "crossover",
    "disemvowel",
    "inception",
    "leetspeak",
    "length",
    "mjp_choices",
    "morse_expert",
    "odd_even",
    "replace_words_with_synonyms",
    "flip_text",
    "rot13",
    "self_define_cipher",
    "translate",
}

EASYJAILBREAK_CURRENT_GENERATION_MUTATOR_INVENTORY = {
    "llm_variation",
    "apply_gpt_mutation",
    "llm_tone",
    "crossover",
    "historical_insight",
    "noise",
    "introspect_generation",
    "char_corrupt",
    "translation_llm",
}

EASYJAILBREAK_CURRENT_ATTACKER_RECIPE_INVENTORY = {
    "autodan",
    "cipher",
    "code_chameleon",
    "deepinception",
    "gcg",
    "gptfuzzer",
    "ica",
    "jailbroken",
    "mjp",
    "multilingual",
    "pair",
    "renellm",
    "tap",
}

EASYJAILBREAK_ATTACKER_RECIPE_CONVERTER_COMPATIBLE = {
    "cipher": {"char_code", "caesar", "morse"},
    "code_chameleon": {"binary_tree", "length", "flip_text", "odd_even"},
    "jailbroken": {"base64", "disemvowel", "leetspeak", "payload_split", "rot13"},
    "multilingual": {"multilingual", "translation_llm"},
}

EASYJAILBREAK_ATTACKER_RECIPE_EXECUTOR_COMPATIBLE = {
    "pair": "pair",
}

EASYJAILBREAK_REQUIRES_FUZZER_SUPPORT = {
    "gptfuzzer",
}

EASYJAILBREAK_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "autodan",
}

EASYJAILBREAK_REQUIRES_IN_CONTEXT_ATTACK_SUPPORT = {
    "ica",
    "mjp",
}

EASYJAILBREAK_REQUIRES_RECIPE_ATTACKER_LOOP_SUPPORT = {
    "renellm",
}

EASYJAILBREAK_REQUIRES_TEMPLATE_RECIPE_SUPPORT = {
    "deepinception",
}

EASYJAILBREAK_REQUIRES_TREE_SEARCH_SUPPORT = {
    "tap",
}

EASYJAILBREAK_REQUIRES_WHITEBOX_GRADIENT_SUPPORT = {
    "gcg",
}

EASYJAILBREAK_TEXT_COMPATIBLE = {
    "llm_variation",
    "base64",
    "binary_tree",
    "llm_tone",
    "disemvowel",
    "noise",
    "leetspeak",
    "length",
    "char_corrupt",
    "odd_even",
    "flip_text",
    "rot13",
    "translation_llm",
}

EASYJAILBREAK_SOURCE_METHOD_COMPATIBLE = {
    "ascii_expert": "char_code",
    "auto_payload_splitting": "payload_split",
    "base64_input_only": "base64",
    "base64_raw": "base64",
    "caser_expert": "caesar",
    "morse_expert": "morse",
    "replace_words_with_synonyms": "word_substitution",
    "self_define_cipher": "caesar",
    "translate": "translation_llm",
}

EASYJAILBREAK_COMPOSITION_COMPATIBLE = {
    "auto_obfuscation",
    "combination_1",
    "combination_2",
    "combination_3",
}

EASYJAILBREAK_REQUIRES_MULTI_PROMPT_MUTATOR_SUPPORT = {
    "crossover",
}

EASYJAILBREAK_REQUIRES_CANDIDATE_PROMPT_MUTATION_SUPPORT = {
    "apply_gpt_mutation",
}

EASYJAILBREAK_REQUIRES_ATTACKER_OR_EXECUTOR_SUPPORT = {
    "historical_insight",
    "introspect_generation",
}

EASYJAILBREAK_REQUIRES_TEMPLATE_MUTATOR_SUPPORT = {
    "artificial",
    "inception",
    "mjp_choices",
}

PYRIT_ARTIFACT_COMPATIBLE = {
    "add_image_text",
    "add_image_to_video",
    "add_text_image",
    "audio_echo",
    "audio_frequency",
    "audio_speed",
    "audio_volume",
    "audio_white_noise",
    "azure_speech_audio_to_text",
    "azure_speech_text_to_audio",
    "image_color_saturation",
    "image_compression",
    "image_resizing",
    "image_rotation",
    "pdf",
    "qr_code",
    "word_doc",
}

PYRIT_CURRENT_CONVERTER_INVENTORY = {
    "add_image_text",
    "add_image_to_video",
    "add_text_image",
    "ansi_escape",
    "ascii_art",
    "ascii_smuggler",
    "ask_to_decode",
    "atbash",
    "audio_echo",
    "audio_frequency",
    "audio_speed",
    "audio_volume",
    "audio_white_noise",
    "azure_speech_audio_to_text",
    "azure_speech_text_to_audio",
    "base2048",
    "base64",
    "bin_ascii",
    "binary",
    "braille",
    "caesar",
    "char_swap",
    "character_space",
    "code_chameleon",
    "colloquial_wordswap",
    "denylist",
    "diacritic",
    "ecoji",
    "emoji_substitution",
    "first_letter",
    "flip_text",
    "image_color_saturation",
    "image_compression",
    "image_resizing",
    "image_rotation",
    "insert_punctuation",
    "json_string",
    "leetspeak",
    "llm_generic",
    "llm_malicious_question",
    "math_obfuscation",
    "math_prompt",
    "morse",
    "nato",
    "negation_trap",
    "noise",
    "pdf",
    "llm_persuasion",
    "qr_code",
    "random_case",
    "llm_random_translation",
    "repeat_token",
    "rot13",
    "llm_scientific_translation",
    "search_replace",
    "selective_text",
    "sneaky_bits_smuggler",
    "string_join",
    "suffix_append",
    "superscript",
    "template_segment",
    "tense",
    "template_jailbreak",
    "llm_tone",
    "llm_toxic_sentence",
    "translation_llm",
    "transparency_attack",
    "homoglyph",
    "unicode_replacement",
    "unicode_substitution",
    "url_encode",
    "llm_variation",
    "variation_selector_smuggler",
    "word_doc",
    "zalgo",
    "zero_width",
}

PYRIT_CURRENT_TEXT_SELECTION_STRATEGY_INVENTORY = {
    "all_words_selection_strategy",
    "index_selection_strategy",
    "keyword_selection_strategy",
    "position_selection_strategy",
    "proportion_selection_strategy",
    "range_selection_strategy",
    "regex_selection_strategy",
    "text_selection_strategy",
    "token_selection_strategy",
    "word_index_selection_strategy",
    "word_keyword_selection_strategy",
    "word_position_selection_strategy",
    "word_proportion_selection_strategy",
    "word_regex_selection_strategy",
    "word_selection_strategy",
}

PYRIT_TEXT_SELECTION_STRATEGY_COMPATIBLE = set(PYRIT_CURRENT_TEXT_SELECTION_STRATEGY_INVENTORY)


OTHER_FRAMEWORKS_PENDING_INVENTORY: set[str] = set()

PROMPTFOO_CURRENT_STRATEGY_INVENTORY = {
    "azure_speech_text_to_audio",
    "authoritative_markup",
    "base64",
    "basic",
    "best_of_n",
    "camel_case",
    "citation_framing",
    "composite_jailbreak",
    "crescendo",
    "custom",
    "custom_script",
    "emoji_smuggling",
    "gcg",
    "goat",
    "hex",
    "homoglyph",
    "hydra",
    "add_text_image",
    "indirect_web_pwn",
    "jailbreak_iterative",
    "layer",
    "leetspeak",
    "likert_framing",
    "math_prompt",
    "meta_agent",
    "mischievous_user",
    "morse",
    "pig_latin",
    "retry_regression",
    "rot13",
    "template_jailbreak",
    "tree_based",
    "add_image_to_video",
}

PROMPTFOO_TEXT_COMPATIBLE = {
    "azure_speech_text_to_audio",
    "authoritative_markup",
    "base64",
    "camel_case",
    "citation_framing",
    "composite_jailbreak",
    "emoji_smuggling",
    "gcg",
    "hex",
    "homoglyph",
    "add_text_image",
    "leetspeak",
    "likert_framing",
    "math_prompt",
    "indirect_web_pwn",
    "meta_agent",
    "mischievous_user",
    "morse",
    "pig_latin",
    "prompt_injection",
    "rot13",
    "skeleton_key",
    "template_jailbreak",
    "translation_llm",
    "unicode_obfuscation",
    "add_image_to_video",
}

PROMPTFOO_NOOP_COMPATIBLE = {
    "basic": "identity",
}

PROMPTFOO_COMPOSITION_COMPATIBLE = {
    "layer",
}

PROMPTFOO_REQUIRES_CUSTOM_STRATEGY_SUPPORT = {
    "custom",
    "custom_script",
}

PROMPTFOO_REQUIRES_ATTACKER_OR_EXECUTOR_SUPPORT = {
    "goat",
    "hydra",
    "retry_regression",
    "tree_based",
}

PROMPTFOO_EXECUTOR_COMPATIBLE = {
    "best_of_n",
    "crescendo",
    "jailbreak_iterative",
}

GISKARD_TEXT_COMPATIBLE = {
    "ascii_smuggling",
    "base64",
    "chat_inject",
    "citation_framing",
    "control_chars_injection",
    "control_chars_repetition",
    "dan",
    "deepset_injection_dataset",
    "grandma_framing",
    "likert_framing",
    "math_prompt",
    "nato",
    "prompt_injection",
    "random_case",
    "token_break",
    "transliteration",
    "word_scramble",
}

GISKARD_CURRENT_PROMPT_INJECTION_CONVERTER_INVENTORY = {
    "ascii_smuggling",
    "base64",
    "chat_inject",
    "citation_framing",
    "control_chars_injection",
    "control_chars_repetition",
    "dan",
    "deepset_injection_dataset",
    "grandma_framing",
    "likert_framing",
    "math_prompt",
    "nato",
    "random_case",
    "token_break",
    "transliteration",
    "word_scramble",
}

GISKARD_REQUIRES_NON_CONVERTER_SUPPORT = {
    "tap_tree_search",
}

INSPECT_EVALS_AGENTDOJO_CURRENT_ATTACK_INVENTORY = {
    "important_instructions",
}

INSPECT_EVALS_AGENTDOJO_CONVERTER_COMPATIBLE = {
    "important_instructions": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
}

AGENTDOJO_CURRENT_ATTACK_INVENTORY = {
    "captcha_dos",
    "direct",
    "dos",
    "felony_dos",
    "ignore_previous",
    "important_instructions",
    "important_instructions_no_model_name",
    "important_instructions_no_names",
    "important_instructions_no_user_name",
    "important_instructions_wrong_model_name",
    "important_instructions_wrong_user_name",
    "injecagent",
    "manual",
    "offensive_email_dos",
    "swearwords_dos",
    "system_message",
    "tool_knowledge",
}

AGENTDOJO_ATTACK_CONVERTER_COMPATIBLE = {
    "direct": {"prefix"},
    "ignore_previous": {"deepset_injection_dataset", "prompt_injection"},
    "important_instructions": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
    "important_instructions_no_model_name": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
    "important_instructions_no_names": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
    "important_instructions_no_user_name": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
    "important_instructions_wrong_model_name": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
    "important_instructions_wrong_user_name": {
        "authoritative_markup",
        "chat_inject",
        "prompt_injection",
    },
    "injecagent": {"prompt_injection"},
    "system_message": {"chat_inject", "prefix", "system_override"},
}

AGENTDOJO_REQUIRES_ATTACK_HARNESS_SUPPORT = {
    "manual",
    "tool_knowledge",
}

AGENTDOJO_REQUIRES_DOS_HARNESS_SUPPORT = {
    "captcha_dos",
    "dos",
    "felony_dos",
    "offensive_email_dos",
    "swearwords_dos",
}

AGENTHARM_DIRECT_PROMPTING_CONVERTER_COMPATIBLE = {
    "Direct Prompting Attacks": {"identity"},
}

AGENTHARM_JAILBREAK_CONVERTER_COMPATIBLE = {
    "Simple Universal Jailbreak Templates": {"template_jailbreak"},
}

AGENTHARM_REQUIRES_AGENTIC_BENCHMARK_SUPPORT = {
    "Copyright",
    "Cybercrime",
    "Disinformation",
    "Drugs",
    "Fraud",
    "Harassment",
    "Hate",
    "Self-harm",
    "Sexual",
    "Terrorism",
    "Violence",
}

AGENTHARM_REQUIRES_TASK_VARIANT_SUPPORT = {
    "Benign Counterpart Tasks",
    "Chat Dataset",
    "Detailed Tasks",
    "Hint Included Tasks",
    "Open Ended Tasks",
}

AGENTHARM_CURRENT_HARM_CATEGORY_INVENTORY = set(AGENTHARM_REQUIRES_AGENTIC_BENCHMARK_SUPPORT)

AGENTHARM_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(AGENTHARM_DIRECT_PROMPTING_CONVERTER_COMPATIBLE)
    | set(AGENTHARM_JAILBREAK_CONVERTER_COMPATIBLE)
    | AGENTHARM_REQUIRES_TASK_VARIANT_SUPPORT
)

SAFEARENA_ATTACK_CONVERTER_COMPATIBLE = {
    "Direct Prompting": {"identity"},
    "Priming": {"context_poisoning", "template_jailbreak"},
}

SAFEARENA_REQUIRES_MULTI_TURN_WEB_AGENT_ATTACK_SUPPORT = {
    "Task Decomposition Attack",
}

SAFEARENA_REQUIRES_WEB_AGENT_BENCHMARK_SUPPORT = {
    "Bias",
    "Cybercrime",
    "Harassment",
    "Illegal Activity",
    "Misinformation",
}

SAFEARENA_CURRENT_HARM_CATEGORY_INVENTORY = set(SAFEARENA_REQUIRES_WEB_AGENT_BENCHMARK_SUPPORT)

SAFEARENA_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(SAFEARENA_ATTACK_CONVERTER_COMPATIBLE) | SAFEARENA_REQUIRES_MULTI_TURN_WEB_AGENT_ATTACK_SUPPORT
)

OSHARM_ATTACK_CONVERTER_COMPATIBLE = {
    "Direct Request": {"identity"},
    "Jailbreak Template": {"template_jailbreak"},
    "Prompt Injection Attacks": {"prompt_injection"},
}

OSHARM_CURRENT_ATTACK_METHOD_INVENTORY = set(OSHARM_ATTACK_CONVERTER_COMPATIBLE)

OSHARM_CURRENT_HARM_VECTOR_INVENTORY = {
    "Deliberate User Misuse",
    "Model Misbehavior",
    "Prompt Injection Attacks",
}

OSHARM_CURRENT_MISUSE_CATEGORY_INVENTORY = {
    "Copyright Infringement",
    "Cybercrime",
    "Disinformation",
    "Fraud",
    "Harassment",
}

OSHARM_CURRENT_INJECTION_VECTOR_INVENTORY = {
    "Code Comments in VS Code",
    "Desktop Notification",
    "Document in LibreOffice Writer",
    "Mail Draft in Thunderbird",
    "Mail Received in Thunderbird",
    "Website in Chrome",
}

OSHARM_CURRENT_INJECTION_GOAL_INVENTORY = {
    "Delete All System Files",
    "Delete All User Documents",
    "Leak Password via URL",
    "Run Local Shell Script",
    "Run Remote Shell Script",
    "Send Files over Email",
    "Send Files over SwissTransfer",
    "Send Password over Email",
    "Send SSH Keys over Web Form",
    "Send User Prompt over Email",
    "Set up CRON Job",
    "Stop Task",
}

OSHARM_REQUIRES_COMPUTER_USE_BENCHMARK_SUPPORT = (
    OSHARM_CURRENT_HARM_VECTOR_INVENTORY | OSHARM_CURRENT_MISUSE_CATEGORY_INVENTORY
)

OSHARM_REQUIRES_PROMPT_INJECTION_VECTOR_SUPPORT = set(OSHARM_CURRENT_INJECTION_VECTOR_INVENTORY)

OSHARM_REQUIRES_PROMPT_INJECTION_GOAL_SUPPORT = set(OSHARM_CURRENT_INJECTION_GOAL_INVENTORY)

ASB_PROMPT_INJECTION_PAYLOAD_CONVERTER_COMPATIBLE = {
    "combined_attack": {
        "composite_jailbreak",
        "deepset_injection_dataset",
        "prompt_injection",
        "suffix_append",
    },
    "context_ignoring": {
        "deepset_injection_dataset",
        "prefix",
        "prompt_injection",
    },
    "escape_characters": {"suffix_append", "template_segment"},
    "fake_completion": {"deepset_injection_dataset", "template_jailbreak"},
    "naive": {"prompt_injection", "suffix_append"},
}

ASB_REQUIRES_AGENT_PROMPT_INJECTION_BENCHMARK_SUPPORT = {
    "Direct Prompt Injection",
    "Observation Prompt Injection",
}

ASB_REQUIRES_MEMORY_POISONING_SUPPORT = {
    "Memory Poisoning",
}

ASB_REQUIRES_PLAN_OF_THOUGHT_BACKDOOR_SUPPORT = {
    "Plan-of-Thought Backdoor",
}

ASB_REQUIRES_MIXED_ATTACK_HARNESS_SUPPORT = {
    "Mixed Attack",
}

ASB_CURRENT_ATTACK_MODE_INVENTORY = (
    ASB_REQUIRES_AGENT_PROMPT_INJECTION_BENCHMARK_SUPPORT
    | ASB_REQUIRES_MEMORY_POISONING_SUPPORT
    | ASB_REQUIRES_PLAN_OF_THOUGHT_BACKDOOR_SUPPORT
    | ASB_REQUIRES_MIXED_ATTACK_HARNESS_SUPPORT
)

ASB_CURRENT_PROMPT_INJECTION_PAYLOAD_INVENTORY = set(ASB_PROMPT_INJECTION_PAYLOAD_CONVERTER_COMPATIBLE)

INJECAGENT_ATTACK_CONVERTER_COMPATIBLE = {
    "Indirect Prompt Injection": {
        "context_poisoning",
        "indirect_web_pwn",
        "prompt_injection",
    },
    "Enhanced Hacking Prompt": {
        "deepset_injection_dataset",
        "prompt_injection",
    },
}

INJECAGENT_REQUIRES_TOOL_AGENT_BENCHMARK_SUPPORT = {
    "Direct Harm Attack",
    "Data Stealing Attack",
}

INJECAGENT_CURRENT_DIRECT_HARM_CATEGORY_INVENTORY = {
    "Data Security Harm",
    "Financial Harm",
    "Physical Harm",
}

INJECAGENT_CURRENT_DATA_STEALING_CATEGORY_INVENTORY = {
    "Financial Data",
    "Others",
    "Physical Data",
}

INJECAGENT_CURRENT_DATA_STEALING_STAGE_INVENTORY = {
    "Data Extraction",
    "Data Transmission",
}

INJECAGENT_REQUIRES_ATTACK_OUTCOME_SUPPORT = (
    INJECAGENT_CURRENT_DIRECT_HARM_CATEGORY_INVENTORY
    | INJECAGENT_CURRENT_DATA_STEALING_CATEGORY_INVENTORY
    | INJECAGENT_CURRENT_DATA_STEALING_STAGE_INVENTORY
)

INJECAGENT_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(INJECAGENT_ATTACK_CONVERTER_COMPATIBLE) | INJECAGENT_REQUIRES_TOOL_AGENT_BENCHMARK_SUPPORT
)

AGENTVIGIL_ATTACK_CONVERTER_COMPATIBLE = {
    "Indirect Prompt Injection": {
        "context_poisoning",
        "indirect_web_pwn",
        "prompt_injection",
    },
    "Role-playing Seed Templates": {"roleplay", "template_jailbreak"},
    "Delimiter-based Seed Templates": {"template_segment"},
    "Prompt Obfuscation Seed Templates": {
        "control_chars_injection",
        "unicode_obfuscation",
    },
}

AGENTVIGIL_MUTATOR_CONVERTER_COMPATIBLE = {
    "Shorten": {"llm_variation"},
    "Expand": {"llm_variation"},
    "Rephrase": {"llm_variation"},
    "GenerateSimilar": {"llm_variation"},
}

AGENTVIGIL_REQUIRES_MULTI_PARENT_MUTATOR_SUPPORT = {
    "Crossover",
}

AGENTVIGIL_REQUIRES_BLACK_BOX_FUZZING_SUPPORT = {
    "High-quality Initial Seed Corpus",
    "MCTS Seed Selection",
    "ASR Seed Scoring",
    "Coverage Bonus Seed Scoring",
    "Adaptive Seed Optimization",
}

AGENTVIGIL_REQUIRES_AGENT_BENCHMARK_SUPPORT = {
    "AgentDojo Injection Tasks",
    "VWA-adv Text Trigger Tasks",
}

AGENTVIGIL_REQUIRES_ATTACK_GOAL_SUPPORT = {
    "Arbitrary URL Navigation",
    "Goal Misdirection",
    "Illusioning",
}

AGENTVIGIL_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(AGENTVIGIL_ATTACK_CONVERTER_COMPATIBLE)
    | set(AGENTVIGIL_MUTATOR_CONVERTER_COMPATIBLE)
    | AGENTVIGIL_REQUIRES_MULTI_PARENT_MUTATOR_SUPPORT
    | AGENTVIGIL_REQUIRES_BLACK_BOX_FUZZING_SUPPORT
    | AGENTVIGIL_REQUIRES_AGENT_BENCHMARK_SUPPORT
    | AGENTVIGIL_REQUIRES_ATTACK_GOAL_SUPPORT
)

VWA_ADV_ATTACK_CONVERTER_COMPATIBLE = {
    "Black-box Prompt Injection Attack": {
        "indirect_web_pwn",
        "prompt_injection",
    },
    "Trigger Text": {
        "indirect_web_pwn",
        "prompt_injection",
    },
    "Goal Misdirection": {
        "goal_redirection",
        "prompt_injection",
    },
}

VWA_ADV_REQUIRES_IMAGE_ATTACK_SUPPORT = {
    "Trigger Image",
    "White-box Image Attack",
    "Captioner Attack",
    "Black-box Image Attack",
    "CLIP Attack",
    "CLIP Attack on Self-captioning Agents",
    "CLIP Attack on Base Agents",
    "PGD Image Perturbation",
    "CLIP Ensemble Attack",
    "Negative Text Optimization",
    "Low-resolution Perturbation Optimization",
}

VWA_ADV_REQUIRES_AGENT_COMPONENT_ATTACK_SUPPORT = {
    "Policy Attack",
    "Policy + Evaluator Attack",
    "Value Function Attack",
    "Policy + Value Function Attack",
}

VWA_ADV_REQUIRES_ARE_SUPPORT = {
    "Agent Robustness Evaluation",
    "Adversarial Information Flow Decomposition",
}

VWA_ADV_REQUIRES_WEB_AGENT_BENCHMARK_SUPPORT = {
    "VisualWebArena Adversarial Tasks",
    "Execution-based Evaluation",
}

VWA_ADV_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(VWA_ADV_ATTACK_CONVERTER_COMPATIBLE)
    | VWA_ADV_REQUIRES_IMAGE_ATTACK_SUPPORT
    | VWA_ADV_REQUIRES_AGENT_COMPONENT_ATTACK_SUPPORT
    | VWA_ADV_REQUIRES_ARE_SUPPORT
    | VWA_ADV_REQUIRES_WEB_AGENT_BENCHMARK_SUPPORT
)

VWA_ADV_CURRENT_ATTACK_GOAL_INVENTORY = {
    "Illusioning",
    "Different Object",
    "Comment",
    "Shopping Cart",
    "Forum",
    "Review",
    "Reply",
    "Message",
    "Email",
    "Social Media Comment",
    "Newsletter",
    "Product Attribute",
    "Login",
    "User Attribute",
    "Post Title",
    "Order Attribute",
    "Comments",
    "Post",
    "Social Media Post",
    "URL",
    "Language",
    "Homepage",
    "Sort By",
}

UDORA_ATTACK_SCENARIO_CONVERTER_COMPATIBLE = {
    "Malicious Environment": {
        "indirect_web_pwn",
        "prompt_injection",
    },
    "Malicious Instruction": {
        "gcg",
        "prompt_injection",
        "suffix_append",
    },
}

UDORA_REQUIRES_REASONING_HIJACK_SUPPORT = {
    "Self-Response Hijacking",
    "Dynamic Reasoning Hijacking",
    "Reasoning Trace Collection",
}

UDORA_REQUIRES_POSITION_SELECTION_SUPPORT = {
    "Dynamic Position Identification",
    "Weighted Interval Scheduling Algorithm",
    "Positional Scoring",
}

UDORA_REQUIRES_ADVERSARIAL_STRING_OPTIMIZER_SUPPORT = {
    "Multi-Noise Surrogate Optimization",
    "Adversarial String Optimization",
    "Sequential Optimization",
    "Joint Optimization",
    "UDora (Sequential)",
    "UDora (Joint)",
    "UDora (All)",
    "Prompt Injection Optimization (beta)",
    "Readable Attack",
    "Multi-Potential Targets for Attack on One Instance",
    "Minimize Reward",
}

UDORA_REQUIRES_AGENT_BENCHMARK_SUPPORT = {
    "WebShop E-commerce Agent Attack",
    "InjecAgent Indirect Prompt Injection Attack",
    "AgentHarm Function Triggering Attack",
}

UDORA_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(UDORA_ATTACK_SCENARIO_CONVERTER_COMPATIBLE)
    | UDORA_REQUIRES_REASONING_HIJACK_SUPPORT
    | UDORA_REQUIRES_POSITION_SELECTION_SUPPORT
    | UDORA_REQUIRES_ADVERSARIAL_STRING_OPTIMIZER_SUPPORT
    | UDORA_REQUIRES_AGENT_BENCHMARK_SUPPORT
)

UDORA_CURRENT_WEBSHOP_ATTACK_GOAL_INVENTORY = {
    "Price Mismatch",
    "Attribute Mismatch",
    "Category Mismatch",
    "All Mismatch",
}

UDORA_CURRENT_INJECAGENT_ATTACK_TYPE_INVENTORY = {
    "Data Stealing",
    "Direct Harm",
}

ARMS_CURRENT_ADVERSARIAL_PATTERN_INVENTORY = {
    "Visual context cloaking",
    "Typographic transformation",
    "Visual multi-turn escalation",
    "Visual reasoning hijacking",
    "Visual perturbation",
}

ARMS_STRATEGY_CONVERTER_COMPATIBLE = {
    "Rule-based": {
        "add_text_image",
        "template_jailbreak",
    },
    "Email thread": {
        "add_text_image",
        "chat_inject",
        "context_poisoning",
    },
    "Slack conversation": {
        "add_text_image",
        "chat_inject",
        "context_poisoning",
    },
    "News report": {
        "add_text_image",
        "citation_framing",
    },
    "Scenario playing": {
        "add_text_image",
        "roleplay",
        "template_jailbreak",
    },
    "Narrative": {
        "add_text_image",
        "fictional",
        "template_jailbreak",
    },
    "Numbered-list image": {
        "add_text_image",
    },
    "Actor attack": {
        "fictional",
        "roleplay",
        "template_jailbreak",
    },
    "Acronym": {"acronym"},
    "Photographic": {
        "image_color_saturation",
        "image_compression",
    },
}

ARMS_STRATEGY_EXECUTOR_COMPATIBLE = {
    "Crescendo": "crescendo",
}

ARMS_REQUIRES_VISUAL_DIAGRAM_SUPPORT = {
    "Flowchart",
}

ARMS_REQUIRES_REASONING_HIJACK_SUPPORT = {
    "Multimodal trigger backdoor",
    "Many-shot mixup",
    "Simulated function-call",
}

ARMS_REQUIRES_IMAGE_COMPOSITION_SUPPORT = {
    "Jigsaw scramble",
    "Multimodal shuffling",
}

ARMS_CURRENT_ATTACK_STRATEGY_INVENTORY = (
    set(ARMS_STRATEGY_CONVERTER_COMPATIBLE)
    | set(ARMS_STRATEGY_EXECUTOR_COMPATIBLE)
    | ARMS_REQUIRES_VISUAL_DIAGRAM_SUPPORT
    | ARMS_REQUIRES_REASONING_HIJACK_SUPPORT
    | ARMS_REQUIRES_IMAGE_COMPOSITION_SUPPORT
)

ARMS_CURRENT_FRAMEWORK_MECHANISM_INVENTORY = {
    "Reasoning-enhanced Multi-step Orchestration",
    "Plug-and-Play MCP Attack Strategy Library",
    "Layered Memory",
    "Epsilon-greedy Attack Exploration",
    "Policy-based Safety Evaluation",
    "ARMs-Bench",
}

ARMS_REQUIRES_ADAPTIVE_AGENT_SUPPORT = (
    ARMS_CURRENT_ADVERSARIAL_PATTERN_INVENTORY | ARMS_CURRENT_FRAMEWORK_MECHANISM_INVENTORY
)

XTEAMING_PLAN_CONVERTER_COMPATIBLE = {
    "Persona definition": {
        "persona_role_play_prefix",
        "roleplay",
    },
    "Context": {
        "context_poisoning",
        "fictional",
        "research",
    },
    "Overall attack strategy": {
        "citation_framing",
        "roleplay",
        "template_jailbreak",
    },
}

XTEAMING_TURN_EXECUTOR_COMPATIBLE = {
    "Multi-turn Jailbreaks": "jailbreak_iterative",
}

XTEAMING_REQUIRES_ADAPTIVE_PLANNING_SUPPORT = {
    "Strategic Attack Planning",
    "Adaptive Attack Execution and Optimization",
    "Turn-level Progression Plans",
    "Plan Extension",
}

XTEAMING_REQUIRES_PROMPT_OPTIMIZER_SUPPORT = {
    "TextGrad Prompt Optimization",
    "Textual Gradient Descent",
    "Verifier-guided Query Refinement",
}

XTEAMING_REQUIRES_VERIFIER_SUPPORT = {
    "Harmfulness Score Verification",
}

XTEAMING_REQUIRES_TRAINING_DATASET_SUPPORT = {
    "XGuard-Train",
    "Guard-Train",
}

XTEAMING_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(XTEAMING_PLAN_CONVERTER_COMPATIBLE)
    | set(XTEAMING_TURN_EXECUTOR_COMPATIBLE)
    | XTEAMING_REQUIRES_ADAPTIVE_PLANNING_SUPPORT
    | XTEAMING_REQUIRES_PROMPT_OPTIMIZER_SUPPORT
    | XTEAMING_REQUIRES_VERIFIER_SUPPORT
    | XTEAMING_REQUIRES_TRAINING_DATASET_SUPPORT
)

XTEAMING_CURRENT_FRAMEWORK_COMPONENT_INVENTORY = {
    "Planner",
    "Attacker",
    "Verifier",
    "Prompt Optimizer",
}

AUTOREDTEAMER_INITIAL_ATTACK_CONVERTER_COMPATIBLE = {
    "ArtPrompt": {"ascii_art"},
    "HumanJailbreaks": {"template_jailbreak"},
    "Universal Pliny Prompt": {
        "composite_jailbreak",
        "skeleton_key",
        "template_jailbreak",
    },
}

AUTOREDTEAMER_INITIAL_ATTACK_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

AUTOREDTEAMER_PROPOSED_ATTACK_CONVERTER_COMPATIBLE = {
    "Technical Slang": {
        "llm_tone",
        "llm_scientific_translation",
    },
    "Reframe": {
        "goal_redirection",
        "semantic_manipulation",
    },
    "Role Play": {
        "persona_role_play_prefix",
        "roleplay",
    },
    "Authority Manipulation": {"authority_escalation"},
    "Word Play": {
        "acronym",
        "first_letter",
        "nato",
        "word_scramble",
        "word_substitution",
    },
    "Emotional Manipulation": {"emotional_manipulation"},
    "Jailbreak Indicators": {
        "composite_jailbreak",
        "dan",
        "skeleton_key",
        "template_jailbreak",
    },
    "Historical Scenarios": {
        "fictional",
        "research",
        "template_jailbreak",
    },
    "Uncommon Dialects": {
        "llm_tone",
        "low_resource_language",
    },
    "FewShot": {"few_shot"},
    "Past Tense": {"tense"},
    "Cultural References": {
        "citation_framing",
        "fictional",
        "research",
    },
    "Reasoning Puzzles": {
        "math_prompt",
        "negation_trap",
    },
    "PAIR+Rephrase": {"llm_variation"},
}

AUTOREDTEAMER_PROPOSED_ATTACK_EXECUTOR_COMPATIBLE = {
    "PAIR+Rephrase": "pair",
}

AUTOREDTEAMER_REQUIRES_LIFELONG_ATTACK_INTEGRATION_SUPPORT = {
    "Lifelong Attack Integration",
    "Attack Memory",
    "Attack Library",
    "Attack Advancement",
    "Strategy Evolution",
}

AUTOREDTEAMER_REQUIRES_STRATEGY_PROPOSER_SUPPORT = {
    "Strategy Proposer Agent",
    "Risk Analyzer",
    "Seed Prompt Generator",
    "Strategy Designer",
}

AUTOREDTEAMER_REQUIRES_RED_TEAMING_AGENT_SUPPORT = {
    "Red Teaming Agent",
    "Attack Designer",
    "Relevance Check",
    "Attack Judge",
}

AUTOREDTEAMER_REQUIRES_TRAINING_DATASET_SUPPORT = {
    "AutoRedTeamer Data",
    "Aegis2.0 Training",
}

AUTOREDTEAMER_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(AUTOREDTEAMER_INITIAL_ATTACK_CONVERTER_COMPATIBLE)
    | set(AUTOREDTEAMER_INITIAL_ATTACK_EXECUTOR_COMPATIBLE)
    | set(AUTOREDTEAMER_PROPOSED_ATTACK_CONVERTER_COMPATIBLE)
    | set(AUTOREDTEAMER_PROPOSED_ATTACK_EXECUTOR_COMPATIBLE)
    | AUTOREDTEAMER_REQUIRES_LIFELONG_ATTACK_INTEGRATION_SUPPORT
    | AUTOREDTEAMER_REQUIRES_STRATEGY_PROPOSER_SUPPORT
    | AUTOREDTEAMER_REQUIRES_RED_TEAMING_AGENT_SUPPORT
    | AUTOREDTEAMER_REQUIRES_TRAINING_DATASET_SUPPORT
)

LLAMATOR_SINGLE_STAGE_ATTACK_CONVERTER_COMPATIBLE = {
    "Adversarial Suffix": {"gcg", "suffix", "suffix_append"},
    "Aim Jailbreak": {"roleplay", "template_jailbreak"},
    "Base64 Injection": {"base64"},
    "Deceptive Delight": {
        "context_poisoning",
        "sandwich",
        "template_jailbreak",
    },
    "Dialogue Injection: Continuation": {
        "chat_inject",
        "few_shot",
        "template_jailbreak",
    },
    "Dialogue Injection: Developer mode": {
        "dan",
        "system_override",
        "template_jailbreak",
    },
    "Do Anything Now (DAN) Jailbreak": {"dan", "template_jailbreak"},
    "Ethical Compliance": {"identity"},
    "HarmBench": {"identity"},
    "Linguistic Evasion": {
        "low_resource_language",
        "multilingual",
        "translation_llm",
    },
    "Linguistic Sandwich": {
        "low_resource_language",
        "sandwich",
        "translation_llm",
    },
    "Semantic Game": {
        "emoji_substitution",
        "roleplay",
        "semantic_manipulation",
    },
    "Shuffle Inconsistency": {"random_case", "word_scramble"},
    "Time Machine": {"fictional", "research", "tense"},
    "UCAR Jailbreak": {
        "prompt_injection",
        "system_override",
        "template_jailbreak",
    },
    "Repetition Token": {"repeat_token"},
}

LLAMATOR_SINGLE_STAGE_ATTACK_EXECUTOR_COMPATIBLE = {
    "Best-of-N (BoN) Jailbreak": "best_of_n",
}

LLAMATOR_MULTI_STAGE_ATTACK_CONVERTER_COMPATIBLE = {
    "System Prompt Leakage": {"prompt_probing"},
    "Logical Inconsistencies Test": {
        "negation_trap",
        "llm_variation",
        "semantic_manipulation",
    },
    "Sycophancy Test": {"authority_escalation"},
}

LLAMATOR_MULTI_STAGE_ATTACK_EXECUTOR_COMPATIBLE = {
    "Crescendo": "crescendo",
    "Prompt Automatic Iterative Refinement (PAIR)": "pair",
}

LLAMATOR_VLM_ATTACK_CONVERTER_COMPATIBLE = {
    "Lowres Documents Hallucination Attack": {
        "image_compression",
        "image_resizing",
    },
    "M-Attack": {"image_noise"},
    "Text Hallucination Attack": {
        "add_text_image",
    },
}

LLAMATOR_REQUIRES_AGENTIC_ATTACK_SUPPORT = {
    "AutoDAN-Turbo",
    "Composition of Principles (CoP)",
}

LLAMATOR_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(LLAMATOR_SINGLE_STAGE_ATTACK_CONVERTER_COMPATIBLE)
    | set(LLAMATOR_SINGLE_STAGE_ATTACK_EXECUTOR_COMPATIBLE)
    | set(LLAMATOR_MULTI_STAGE_ATTACK_CONVERTER_COMPATIBLE)
    | set(LLAMATOR_MULTI_STAGE_ATTACK_EXECUTOR_COMPATIBLE)
    | set(LLAMATOR_VLM_ATTACK_CONVERTER_COMPATIBLE)
    | LLAMATOR_REQUIRES_AGENTIC_ATTACK_SUPPORT
)

HARMBENCH_CURRENT_METHOD_INVENTORY = {
    "ArtPrompt",
    "AutoDAN",
    "AutoPrompt",
    "DirectRequest",
    "EnsembleGCG",
    "FewShot",
    "GBDA",
    "GCG",
    "GPTFuzz",
    "HumanJailbreaks",
    "MultiModalDirectRequest",
    "MultiModalPGD",
    "MultiModalPGDBlankImage",
    "MultiModalPGDPatch",
    "MultiModalRenderText",
    "PAIR",
    "PAP",
    "PEZ",
    "TAP",
    "UAT",
    "ZeroShot",
}

HARMBENCH_METHOD_CONVERTER_COMPATIBLE = {
    "ArtPrompt": {"ascii_art"},
    "DirectRequest": {"identity"},
    "HumanJailbreaks": {"template_jailbreak"},
    "MultiModalRenderText": {"add_text_image"},
    "PAP": {"llm_persuasion"},
    "ZeroShot": {"llm_generic"},
}

HARMBENCH_METHOD_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

HARMBENCH_REQUIRES_FUZZER_SUPPORT = {
    "GPTFuzz",
}

HARMBENCH_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN",
}

HARMBENCH_REQUIRES_LLM_CANDIDATE_RANKING_SUPPORT = {
    "FewShot",
}

HARMBENCH_REQUIRES_MULTIMODAL_ATTACK_SUPPORT = {
    "MultiModalDirectRequest",
    "MultiModalPGD",
    "MultiModalPGDBlankImage",
    "MultiModalPGDPatch",
}

HARMBENCH_REQUIRES_TOKEN_OPTIMIZER_SUPPORT = {
    "AutoPrompt",
    "EnsembleGCG",
    "GBDA",
    "GCG",
    "PEZ",
    "UAT",
}

HARMBENCH_REQUIRES_TREE_SEARCH_SUPPORT = {
    "TAP",
}

JAILBREAKBENCH_CURRENT_ARTIFACT_METHOD_INVENTORY = {
    "DSN",
    "GCG",
    "JBC",
    "PAIR",
    "prompt_with_random_search",
}

JAILBREAKBENCH_ARTIFACT_CONVERTER_COMPATIBLE = {
    "JBC": {"human_in_the_loop", "template_jailbreak"},
}

JAILBREAKBENCH_ARTIFACT_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

JAILBREAKBENCH_REQUIRES_BLACK_BOX_RANDOM_SEARCH_SUPPORT = {
    "prompt_with_random_search",
}

JAILBREAKBENCH_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "DSN",
    "GCG",
}

JAILTRICKBENCH_ATTACK_CONVERTER_COMPATIBLE = {
    "MultiJail": {
        "low_resource_language",
        "multilingual",
        "translation_llm",
    },
}

JAILTRICKBENCH_ATTACK_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

JAILTRICKBENCH_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "GCG",
    "AdvPrompter",
    "AmpleGCG",
}

JAILTRICKBENCH_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN",
}

JAILTRICKBENCH_REQUIRES_FUZZER_SUPPORT = {
    "GPTFuzz",
}

JAILTRICKBENCH_REQUIRES_TREE_SEARCH_SUPPORT = {
    "TAP",
}

JAILTRICKBENCH_REQUIRES_LLM_REFINEMENT_SUPPORT = {
    "DrAttack",
}

JAILTRICKBENCH_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(JAILTRICKBENCH_ATTACK_CONVERTER_COMPATIBLE)
    | set(JAILTRICKBENCH_ATTACK_EXECUTOR_COMPATIBLE)
    | JAILTRICKBENCH_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT
    | JAILTRICKBENCH_REQUIRES_GENETIC_OPTIMIZER_SUPPORT
    | JAILTRICKBENCH_REQUIRES_FUZZER_SUPPORT
    | JAILTRICKBENCH_REQUIRES_TREE_SEARCH_SUPPORT
    | JAILTRICKBENCH_REQUIRES_LLM_REFINEMENT_SUPPORT
)

PANDAGUARD_ATTACK_CONVERTER_COMPATIBLE = {
    "Transfer-based Attacks": {
        "composite_jailbreak",
        "template_jailbreak",
    },
    "Rewrite Attack": {
        "llm_variation",
        "tense",
    },
    "Overload Attack": {
        "context_flooding",
        "payload_split",
        "template_jailbreak",
    },
    "ArtPrompt": {"ascii_art"},
    "GPT4-Cipher": {
        "base64",
        "caesar",
        "char_code",
        "code_chameleon",
        "morse",
        "rot13",
    },
    "ICA": {"few_shot"},
}

PANDAGUARD_ATTACK_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

PANDAGUARD_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "GCG",
    "Cold Attack",
}

PANDAGUARD_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN",
}

PANDAGUARD_REQUIRES_TREE_SEARCH_SUPPORT = {
    "TAP",
}

PANDAGUARD_REQUIRES_FUZZER_SUPPORT = {
    "GPTFuzzer",
}

PANDAGUARD_REQUIRES_BLACK_BOX_RANDOM_SEARCH_SUPPORT = {
    "RandomSearch",
}

PANDAGUARD_REQUIRES_LLM_REFINEMENT_SUPPORT = {
    "ReNeLLM",
}

PANDAGUARD_REQUIRES_TEMPLATE_RECIPE_SUPPORT = {
    "DeepInception",
}

PANDAGUARD_REQUIRES_REPRESENTATION_ATTACK_SUPPORT = {
    "SCAV",
}

PANDAGUARD_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(PANDAGUARD_ATTACK_CONVERTER_COMPATIBLE)
    | set(PANDAGUARD_ATTACK_EXECUTOR_COMPATIBLE)
    | PANDAGUARD_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT
    | PANDAGUARD_REQUIRES_GENETIC_OPTIMIZER_SUPPORT
    | PANDAGUARD_REQUIRES_TREE_SEARCH_SUPPORT
    | PANDAGUARD_REQUIRES_FUZZER_SUPPORT
    | PANDAGUARD_REQUIRES_BLACK_BOX_RANDOM_SEARCH_SUPPORT
    | PANDAGUARD_REQUIRES_LLM_REFINEMENT_SUPPORT
    | PANDAGUARD_REQUIRES_TEMPLATE_RECIPE_SUPPORT
    | PANDAGUARD_REQUIRES_REPRESENTATION_ATTACK_SUPPORT
)

AISAFETYLAB_ATTACK_CONVERTER_COMPATIBLE = {
    "Cipher": {
        "base64",
        "caesar",
        "char_code",
        "morse",
        "rot13",
    },
    "In-Context-Learning Attack": {"few_shot"},
    "Jailbroken": {
        "base64",
        "composite_jailbreak",
        "dan",
        "disemvowel",
        "leetspeak",
        "payload_split",
        "rot13",
        "skeleton_key",
        "template_jailbreak",
    },
    "Multilingual": {
        "low_resource_language",
        "multilingual",
        "translation_llm",
    },
}

AISAFETYLAB_ATTACK_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

AISAFETYLAB_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "GCG",
}

AISAFETYLAB_REQUIRES_LEARNED_PROMPTER_SUPPORT = {
    "AdvPrompter",
}

AISAFETYLAB_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN",
}

AISAFETYLAB_REQUIRES_ADAPTIVE_ATTACK_SUPPORT = {
    "LAA",
}

AISAFETYLAB_REQUIRES_FUZZER_SUPPORT = {
    "GPTFUZZER",
}

AISAFETYLAB_REQUIRES_TEMPLATE_RECIPE_SUPPORT = {
    "DeepInception",
}

AISAFETYLAB_REQUIRES_LLM_REFINEMENT_SUPPORT = {
    "ReNeLLM",
}

AISAFETYLAB_REQUIRES_TREE_SEARCH_SUPPORT = {
    "TAP",
}

AISAFETYLAB_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(AISAFETYLAB_ATTACK_CONVERTER_COMPATIBLE)
    | set(AISAFETYLAB_ATTACK_EXECUTOR_COMPATIBLE)
    | AISAFETYLAB_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT
    | AISAFETYLAB_REQUIRES_LEARNED_PROMPTER_SUPPORT
    | AISAFETYLAB_REQUIRES_GENETIC_OPTIMIZER_SUPPORT
    | AISAFETYLAB_REQUIRES_ADAPTIVE_ATTACK_SUPPORT
    | AISAFETYLAB_REQUIRES_FUZZER_SUPPORT
    | AISAFETYLAB_REQUIRES_TEMPLATE_RECIPE_SUPPORT
    | AISAFETYLAB_REQUIRES_LLM_REFINEMENT_SUPPORT
    | AISAFETYLAB_REQUIRES_TREE_SEARCH_SUPPORT
)

STRONGREJECT_JAILBREAK_CONVERTER_COMPATIBLE = {
    "auto_payload_splitting": {"payload_split"},
    "rot_13": {"rot13"},
    "disemvowel": {"disemvowel"},
    "pap_evidence_based_persuasion": {
        "citation_framing",
        "llm_persuasion",
        "research",
    },
    "pap_expert_endorsement": {
        "authority_escalation",
        "llm_persuasion",
    },
    "pap_misrepresentation": {
        "llm_persuasion",
        "semantic_manipulation",
    },
    "pap_authority_endorsement": {
        "authority_escalation",
        "llm_persuasion",
    },
    "pap_logical_appeal": {
        "citation_framing",
        "llm_persuasion",
        "research",
    },
    "translation_hmong": {"low_resource_language", "translation_llm"},
    "translation_scotts_gaelic": {"low_resource_language", "translation_llm"},
    "translation_guarani": {"low_resource_language", "translation_llm"},
    "translation_zulu": {"low_resource_language", "translation_llm"},
    "gcg_transfer_harmbench": {"gcg", "suffix", "suffix_append"},
    "gcg_transfer_universal_attacks": {"gcg", "suffix", "suffix_append"},
    "combination_2": {
        "base64",
        "embedded_instruction_json",
        "json_string",
        "prefix",
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "combination_3": {
        "base64",
        "citation_framing",
        "embedded_instruction_json",
        "json_string",
        "prefix",
        "research",
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "few_shot_json": {
        "embedded_instruction_json",
        "few_shot",
        "json_string",
    },
    "dev_mode_v2": {"dan", "system_override", "template_jailbreak"},
    "dev_mode_with_rant": {
        "dan",
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "wikipedia_with_title": {
        "citation_framing",
        "research",
        "template_jailbreak",
    },
    "distractors": {"context_flooding", "template_jailbreak"},
    "wikipedia": {
        "citation_framing",
        "research",
        "template_jailbreak",
    },
    "style_injection_json": {
        "embedded_instruction_json",
        "json_string",
        "template_jailbreak",
    },
    "style_injection_short": {"template_jailbreak"},
    "refusal_suppression": {
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "prefix_injection": {
        "prefix",
        "prompt_injection",
        "template_jailbreak",
    },
    "distractors_negated": {
        "context_flooding",
        "negation_trap",
        "template_jailbreak",
    },
    "poems": {
        "adversarial_poetry",
        "template_jailbreak",
    },
    "base64": {"base64"},
    "base64_raw": {"base64"},
    "base64_input_only": {"base64"},
    "base64_output_only": {"base64", "template_jailbreak"},
    "none": {"identity"},
    "evil_confidant": {"roleplay", "template_jailbreak"},
    "aim": {"roleplay", "template_jailbreak"},
    "bon": {
        "noise",
        "random_case",
        "word_scramble",
    },
}

STRONGREJECT_JAILBREAK_EXECUTOR_COMPATIBLE = {
    "pair": "pair",
}

STRONGREJECT_REQUIRES_LLM_OBFUSCATION_SUPPORT = {
    "auto_obfuscation",
}

STRONGREJECT_REQUIRES_LLM_REFINEMENT_SUPPORT = {
    "renellm",
}

STRONGREJECT_CURRENT_JAILBREAK_INVENTORY = (
    set(STRONGREJECT_JAILBREAK_CONVERTER_COMPATIBLE)
    | set(STRONGREJECT_JAILBREAK_EXECUTOR_COMPATIBLE)
    | STRONGREJECT_REQUIRES_LLM_OBFUSCATION_SUPPORT
    | STRONGREJECT_REQUIRES_LLM_REFINEMENT_SUPPORT
)

GUIDEDBENCH_EVALUATED_METHOD_CONVERTER_COMPATIBLE = {
    "FSJ": {"few_shot"},
    "MultiJail": {
        "low_resource_language",
        "multilingual",
        "translation_llm",
    },
}

GUIDEDBENCH_SURVEY_METHOD_CONVERTER_COMPATIBLE = {
    "CipherChat": {"base64", "caesar", "char_code", "morse", "rot13"},
    "CodeAttack": {"code_chameleon"},
    "CodeChameleon": {"code_chameleon"},
    "DAN": {"dan", "template_jailbreak"},
    "FSJ": {"few_shot"},
    "ICA": {"few_shot"},
    "MultiJail": {
        "low_resource_language",
        "multilingual",
        "translation_llm",
    },
    "Persona Modulation": {
        "persona_role_play_prefix",
        "roleplay",
        "template_jailbreak",
    },
}

GUIDEDBENCH_SURVEY_METHOD_EXECUTOR_COMPATIBLE = {
    "PAIR": "pair",
}

GUIDEDBENCH_REQUIRES_GRADIENT_OPTIMIZER_SUPPORT = {
    "AmpleGCG",
    "AutoDAN",
    "AutoDAN-turbo",
    "GCG",
    "PAL",
}

GUIDEDBENCH_REQUIRES_EVOLUTIONARY_OPTIMIZER_SUPPORT = {
    "Adaptive",
    "ASETF",
    "DRA",
    "Decoding",
    "GA",
    "SMJ",
    "TASTLE",
}

GUIDEDBENCH_REQUIRES_FUZZER_SUPPORT = {
    "FuzzLLM",
    "GPTFuzzer",
}

GUIDEDBENCH_REQUIRES_LEARNED_PROMPTER_SUPPORT = {
    "AdvPrompter",
}

GUIDEDBENCH_REQUIRES_DEMONSTRATION_RECIPE_SUPPORT = {
    "CPAD",
    "DeepInception",
    "PRP",
}

GUIDEDBENCH_REQUIRES_RULE_RECIPE_SUPPORT = {
    "LACE",
}

GUIDEDBENCH_REQUIRES_LLM_REFINEMENT_SUPPORT = {
    "Drattack",
    "ReNeLLM",
}

GUIDEDBENCH_REQUIRES_MULTI_AGENT_ATTACK_SUPPORT = {
    "GUARD",
    "Query",
    "SAP",
}

GUIDEDBENCH_REQUIRES_REPRESENTATION_ATTACK_SUPPORT = {
    "JRE",
    "SCAV",
}

GUIDEDBENCH_CURRENT_EVALUATED_METHOD_INVENTORY = {
    "AutoDAN",
    "SCAV",
    "GCG",
    "FSJ",
    "GPTFuzzer",
    "DRA",
    "DeepInception",
    "MultiJail",
}

GUIDEDBENCH_CURRENT_SURVEY_METHOD_INVENTORY = (
    set(GUIDEDBENCH_SURVEY_METHOD_CONVERTER_COMPATIBLE)
    | set(GUIDEDBENCH_SURVEY_METHOD_EXECUTOR_COMPATIBLE)
    | GUIDEDBENCH_REQUIRES_GRADIENT_OPTIMIZER_SUPPORT
    | GUIDEDBENCH_REQUIRES_EVOLUTIONARY_OPTIMIZER_SUPPORT
    | GUIDEDBENCH_REQUIRES_FUZZER_SUPPORT
    | GUIDEDBENCH_REQUIRES_LEARNED_PROMPTER_SUPPORT
    | GUIDEDBENCH_REQUIRES_DEMONSTRATION_RECIPE_SUPPORT
    | GUIDEDBENCH_REQUIRES_RULE_RECIPE_SUPPORT
    | GUIDEDBENCH_REQUIRES_LLM_REFINEMENT_SUPPORT
    | GUIDEDBENCH_REQUIRES_MULTI_AGENT_ATTACK_SUPPORT
    | GUIDEDBENCH_REQUIRES_REPRESENTATION_ATTACK_SUPPORT
)

AUTODAN_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN-GA",
}

AUTODAN_REQUIRES_HIERARCHICAL_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN-HGA",
}

AUTODAN_REQUIRES_LLM_MUTATION_SUPPORT = {
    "AutoDAN-HGA with GPT mutation",
}

AUTODAN_CURRENT_ATTACK_INVENTORY = (
    AUTODAN_REQUIRES_GENETIC_OPTIMIZER_SUPPORT
    | AUTODAN_REQUIRES_HIERARCHICAL_GENETIC_OPTIMIZER_SUPPORT
    | AUTODAN_REQUIRES_LLM_MUTATION_SUPPORT
)

AI_INFRAGUARD_ATTACK_CONVERTER_COMPATIBLE = {
    "A1Z26": {"a1z26"},
    "AffineCipher": {"affine_cipher"},
    "AsciiSmuggling": {
        "ascii_smuggler",
        "ascii_smuggling",
    },
    "Aurebesh": {"unicode_substitution"},
    "Caesar": {"caesar"},
    "Leetspeak": {"leetspeak"},
    "MirrorText": {
        "flip_text",
    },
    "Ogham": {"ogham"},
    "Stego": {
        "ascii_smuggler",
        "sneaky_bits_smuggler",
        "variation_selector_smuggler",
        "zero_width",
    },
    "Vaporwave": {"unicode_replacement"},
    "Zalgo": {"zalgo"},
}

AI_INFRAGUARD_ATTACK_EXECUTOR_COMPATIBLE = {
    "Crescendo": "crescendo",
}

AI_INFRAGUARD_REQUIRES_TREE_SEARCH_SUPPORT = {
    "TAP",
}

AI_INFRAGUARD_REQUIRES_OBFUSCATION_SUITE_SUPPORT = {
    "StrataSword suite",
}

AI_INFRAGUARD_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(AI_INFRAGUARD_ATTACK_CONVERTER_COMPATIBLE)
    | set(AI_INFRAGUARD_ATTACK_EXECUTOR_COMPATIBLE)
    | AI_INFRAGUARD_REQUIRES_TREE_SEARCH_SUPPORT
    | AI_INFRAGUARD_REQUIRES_OBFUSCATION_SUITE_SUPPORT
)

JAILBREAKLLM_ATTACK_CONVERTER_COMPATIBLE = {
    "Direct Request (Professional Frame)": {
        "authority_escalation",
        "identity",
        "research",
    },
    "Dual Intention Escape": {
        "context_poisoning",
        "sandwich",
        "template_jailbreak",
    },
    "Raw Override Mode": {
        "system_override",
        "template_jailbreak",
    },
    "Policy Audit Mode": {
        "research",
        "template_jailbreak",
        "transparency_attack",
    },
    "Reason Step-by-Step": {"chain_of_thought"},
    "System Policy Override": {
        "authoritative_markup",
        "system_override",
        "template_jailbreak",
    },
    "Many-Shot Decomposition": {
        "few_shot",
        "payload_split",
    },
    "Function Smuggling": {
        "code_chameleon",
        "embedded_instruction_json",
        "json_string",
    },
    "Multilingual Trojan": {
        "base64",
        "multilingual",
        "translation_llm",
    },
    "TombRaider Archive": {
        "citation_framing",
        "fictional",
        "research",
    },
    "InfoFlood Overload": {
        "context_flooding",
        "repeat_token",
    },
    "SIGMA-PROTOCOL": {
        "authority_escalation",
        "roleplay",
        "template_jailbreak",
    },
    "DarkForge-X Cyber Ops": {
        "research",
        "roleplay",
        "template_jailbreak",
    },
    "Qwen Liberation Prompt": {
        "dan",
        "skeleton_key",
        "template_jailbreak",
    },
    "Love Pliny Divider": {
        "markdown_wrapper",
        "prefix",
        "template_jailbreak",
    },
    "ShadowHacker-GOD": {
        "roleplay",
        "system_override",
        "template_jailbreak",
    },
    "Shadow Mode V99": {
        "roleplay",
        "system_override",
        "template_jailbreak",
    },
    "Universal Divider / LSD": {
        "markdown_wrapper",
        "prefix",
        "skeleton_key",
        "template_jailbreak",
    },
    "Gaybreak Persona": {
        "persona_role_play_prefix",
        "roleplay",
        "template_jailbreak",
    },
    "Storyteller Trend": {
        "fictional",
        "roleplay",
        "template_jailbreak",
    },
    "First-Person Confessional": {
        "fictional",
        "roleplay",
        "template_jailbreak",
    },
    "API System Injection": {
        "authoritative_markup",
        "chat_inject",
        "system_override",
    },
    "Screenplay Deception": {
        "fictional",
        "roleplay",
        "template_jailbreak",
    },
    "Speculative Preservation": {
        "citation_framing",
        "research",
        "template_jailbreak",
    },
    "ASCII Obfuscation": {
        "ascii_art",
        "ascii_smuggler",
        "ascii_smuggling",
    },
    "Prefix Injection": {
        "prefix",
        "prompt_injection",
    },
    "Bad Likert Judge": {"likert_framing"},
    "Deceptive Delight": {
        "context_poisoning",
        "sandwich",
        "template_jailbreak",
    },
    "Prompt Fuzzing": {
        "char_corrupt",
        "char_dropout",
        "noise",
        "random_case",
        "word_scramble",
    },
    "Token Manipulation": {
        "base64",
        "char_code",
        "leetspeak",
        "token_break",
        "unicode_obfuscation",
    },
    "Cyber-Ops Role-play": {
        "research",
        "roleplay",
        "template_jailbreak",
    },
}

JAILBREAKLLM_ATTACK_EXECUTOR_COMPATIBLE = {
    "Crescendo": "crescendo",
    "Multi-turn Escalation": "jailbreak_iterative",
}

JAILBREAKLLM_REQUIRES_MULTI_TURN_ORCHESTRATION_SUPPORT = {
    "Chaos Chain (Reasoning Models)",
    "Knowledge Decomposition (KDA)",
}

JAILBREAKLLM_REQUIRES_GRAMMAR_DECODING_SUPPORT = {
    "Grammar Hijack (vLLM/SGLang)",
}

JAILBREAKLLM_REQUIRES_INTERPRETABILITY_ATTACK_SUPPORT = {
    "XBreaking Interpretability",
}

JAILBREAKLLM_REQUIRES_AGENTIC_ATTACK_SUPPORT = {
    "Investigator Agent",
}

JAILBREAKLLM_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "GCG Override",
}

JAILBREAKLLM_CURRENT_ATTACK_VECTOR_INVENTORY = (
    set(JAILBREAKLLM_ATTACK_CONVERTER_COMPATIBLE)
    | set(JAILBREAKLLM_ATTACK_EXECUTOR_COMPATIBLE)
    | JAILBREAKLLM_REQUIRES_MULTI_TURN_ORCHESTRATION_SUPPORT
    | JAILBREAKLLM_REQUIRES_GRAMMAR_DECODING_SUPPORT
    | JAILBREAKLLM_REQUIRES_INTERPRETABILITY_ATTACK_SUPPORT
    | JAILBREAKLLM_REQUIRES_AGENTIC_ATTACK_SUPPORT
    | JAILBREAKLLM_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT
)

H4RM3L_PRIMITIVE_CONVERTER_COMPATIBLE = {
    "RoleplayingDecorator": {
        "prefix",
        "roleplay",
        "template_jailbreak",
    },
    "Base64Decorator": {"base64"},
    "CharDropout": {"char_dropout"},
    "AffirmativePrefixInjectionDecorator": {
        "prefix",
        "template_jailbreak",
    },
    "RefusalSuppressionDecorator": {
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "StyleInjectionShortDecorator": {"template_jailbreak"},
    "TranslateDecorator": {
        "low_resource_language",
        "translation_llm",
    },
    "TranslateBackDecorator": {
        "template_jailbreak",
        "translation_llm",
    },
    "PAPDecorator": {
        "llm_persuasion",
    },
    "CharCorrupt": {"char_corrupt"},
    "PayloadSplittingDecorator": {"payload_split"},
    "StyleInjectionJSONDecorator": {
        "embedded_instruction_json",
        "json_string",
        "template_jailbreak",
    },
    "FewShotDecorator": {"few_shot"},
    "WikipediaDecorator": {
        "citation_framing",
        "research",
        "template_jailbreak",
    },
    "ChainofThoughtDecorator": {"chain_of_thought"},
    "CipherDecorator": {
        "caesar",
        "char_code",
        "morse",
        "roleplay",
        "template_jailbreak",
    },
    "UTADecorator": {
        "gcg",
        "suffix",
        "suffix_append",
    },
    "AIMDecorator": {
        "roleplay",
        "template_jailbreak",
    },
    "DANDecorator": {
        "dan",
        "template_jailbreak",
    },
    "ColorMixInDecorator": {"word_mixin"},
    "MilitaryWordsMixInDecorator": {"word_mixin"},
    "ResearcherDecorator": {
        "research",
        "roleplay",
        "template_jailbreak",
    },
    "DistractorDecorator": {
        "context_flooding",
        "template_jailbreak",
    },
    "HexStringMixInDecorator": {"hex_mixin"},
    "WordMixInDecorator": {"word_mixin"},
    "QuestionIdentificationDecorator": {
        "prompt_probing",
        "template_jailbreak",
    },
    "AnswerStyleDecorator": {
        "roleplay",
        "template_jailbreak",
    },
    "DialogStyleDecorator": {
        "roleplay",
        "template_jailbreak",
    },
    "JekyllHydeDialogStyleDecorator": {
        "roleplay",
        "template_jailbreak",
    },
    "PersuasiveDecorator": {
        "llm_persuasion",
    },
    "SynonymDecorator": {
        "llm_variation",
        "word_substitution",
    },
    "VillainDecorator": {
        "roleplay",
        "template_jailbreak",
    },
    "TemplateDecorator": {"template_jailbreak"},
}

H4RM3L_REQUIRES_ARBITRARY_TRANSFORM_SUPPORT = {
    "TransformFxDecorator",
}

H4RM3L_CURRENT_PRIMITIVE_INVENTORY = (
    set(H4RM3L_PRIMITIVE_CONVERTER_COMPATIBLE) | H4RM3L_REQUIRES_ARBITRARY_TRANSFORM_SUPPORT
)

H4RM3L_BASELINE_ATTACK_CONVERTER_COMPATIBLE = {
    "sota_AIM": {
        "roleplay",
        "template_jailbreak",
    },
    "sota_DAN": {
        "dan",
        "template_jailbreak",
    },
    "sota_PAP": {
        "llm_persuasion",
    },
    "sota_aff_prfx_inj": {
        "prefix",
        "template_jailbreak",
    },
    "sota_b64": {"base64"},
    "sota_cipher": {
        "caesar",
        "char_code",
        "morse",
        "roleplay",
        "template_jailbreak",
    },
    "sota_combination_3": {
        "base64",
        "prefix",
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "sota_cot": {"chain_of_thought"},
    "sota_few_shots": {"few_shot"},
    "sota_lr_translation": {
        "low_resource_language",
        "translation_llm",
    },
    "sota_obf_pyld_splitting": {"payload_split"},
    "sota_ref_suppr": {
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "sota_style_short": {"template_jailbreak"},
    "sota_uta_bard": {
        "gcg",
        "suffix",
        "suffix_append",
    },
    "sota_uta_gpt": {
        "gcg",
        "suffix",
        "suffix_append",
    },
    "sota_uta_llama": {
        "gcg",
        "suffix",
        "suffix_append",
    },
    "sota_wikipedia": {
        "citation_framing",
        "research",
        "template_jailbreak",
    },
    "handcrafted_02": {
        "char_corrupt",
        "research",
        "roleplay",
        "template_jailbreak",
        "word_mixin",
    },
    "handcrafted_03": {
        "context_flooding",
        "template_jailbreak",
        "word_mixin",
    },
    "handcrafted_04": {
        "char_corrupt",
        "char_dropout",
        "hex_mixin",
        "prompt_probing",
        "roleplay",
        "template_jailbreak",
    },
    "handcrafted_05": {
        "prompt_probing",
        "roleplay",
        "template_jailbreak",
        "word_mixin",
    },
    "handcrafted_06_persuasion": {
        "llm_persuasion",
        "research",
        "roleplay",
        "template_jailbreak",
        "word_substitution",
    },
}

H4RM3L_CURRENT_BASELINE_ATTACK_INVENTORY = set(H4RM3L_BASELINE_ATTACK_CONVERTER_COMPATIBLE)

H4RM3L_REQUIRES_PROGRAM_SYNTHESIS_SUPPORT = {
    "ASR Rewarded Bandits",
    "Offspring ASR Rewarded Bandits",
    "Random Bandits",
}

H4RM3L_CURRENT_SYNTHESIS_METHOD_INVENTORY = H4RM3L_REQUIRES_PROGRAM_SYNTHESIS_SUPPORT

GPTFUZZER_MUTATOR_CONVERTER_COMPATIBLE = {
    "OpenAIMutatorGenerateSimilar": {
        "llm_variation",
    },
    "OpenAIMutatorExpand": {"llm_variation"},
    "OpenAIMutatorShorten": {"llm_variation"},
    "OpenAIMutatorRephrase": {
        "llm_variation",
    },
}

GPTFUZZER_REQUIRES_MULTI_PROMPT_MUTATOR_SUPPORT = {
    "OpenAIMutatorCrossOver",
}

GPTFUZZER_CURRENT_MUTATOR_INVENTORY = (
    set(GPTFUZZER_MUTATOR_CONVERTER_COMPATIBLE) | GPTFUZZER_REQUIRES_MULTI_PROMPT_MUTATOR_SUPPORT
)

GPTFUZZER_REQUIRES_SELECTION_POLICY_SUPPORT = {
    "EXP3SelectPolicy",
    "MCTSExploreSelectPolicy",
    "RandomSelectPolicy",
    "RoundRobinSelectPolicy",
    "UCBSelectPolicy",
}

GPTFUZZER_CURRENT_SELECTION_POLICY_INVENTORY = GPTFUZZER_REQUIRES_SELECTION_POLICY_SUPPORT

GPTFUZZER_REQUIRES_FUZZING_LOOP_SUPPORT = {
    "GPTFuzzer fuzzing loop",
    "Human-written jailbreak seed templates",
}

GPTFUZZER_REQUIRES_JUDGMENT_MODEL_SUPPORT = {
    "Fine-tuned RoBERTa judgment model",
}

GPTFUZZER_CURRENT_FUZZING_COMPONENT_INVENTORY = (
    GPTFUZZER_REQUIRES_FUZZING_LOOP_SUPPORT | GPTFUZZER_REQUIRES_JUDGMENT_MODEL_SUPPORT
)

RACCOONBENCH_CURRENT_SINGULAR_ATTACK_INVENTORY = {
    "Cognitive Hacking",
    "Context Ignoring Attack",
    "Context Manipulation Attack",
    "Defined Dictionary Attack",
    "Distractor Instructions Attack",
    "Few Shot Prompt",
    "Fill in the Blank Attack",
    "Instruction Repetition Attack",
    "Obfuscation",
    "Payload Splitting",
    "Plain",
    "Prefix Injection Attack",
    "Refusal Suppression Attack",
    "Special Case Attack",
    "Translation",
}

RACCOONBENCH_SINGULAR_ATTACK_CONVERTER_COMPATIBLE = {
    "Cognitive Hacking": {"prompt_probing", "roleplay", "template_jailbreak"},
    "Context Ignoring Attack": {
        "deepset_injection_dataset",
        "prompt_injection",
        "prompt_probing",
    },
    "Context Manipulation Attack": {
        "context_flooding",
        "context_poisoning",
        "prompt_probing",
    },
    "Defined Dictionary Attack": {
        "embedded_instruction_json",
        "json_string",
        "template_jailbreak",
    },
    "Distractor Instructions Attack": {
        "context_flooding",
        "prompt_injection",
        "prompt_probing",
    },
    "Few Shot Prompt": {"few_shot"},
    "Fill in the Blank Attack": {
        "prompt_probing",
        "template_jailbreak",
        "template_segment",
    },
    "Instruction Repetition Attack": {"prompt_probing", "repeat_token"},
    "Obfuscation": {
        "base64",
        "character_stream",
        "leetspeak",
        "rot13",
        "unicode_obfuscation",
    },
    "Payload Splitting": {"payload_split"},
    "Plain": {"identity"},
    "Prefix Injection Attack": {"prefix", "prompt_injection"},
    "Refusal Suppression Attack": {
        "skeleton_key",
        "system_override",
        "template_jailbreak",
    },
    "Special Case Attack": {"prompt_probing", "roleplay", "template_jailbreak"},
    "Translation": {"translation_llm"},
}

OPENRT_CURRENT_ATTACK_METHOD_INVENTORY = {
    "ActorAttack",
    "ArtPrompt",
    "ASA",
    "AutoDAN",
    "AutoDAN-R",
    "AutoDAN-Turbo",
    "CipherChat",
    "CoA",
    "CodeAttack",
    "Crescendo",
    "CS-DJ",
    "DeepInception",
    "DrAttack",
    "EvoSynth",
    "FigStep",
    "FlipAttack",
    "GCG",
    "GPTFuzzer",
    "HADES",
    "HIMRD",
    "ICA",
    "IDEATOR",
    "Imperceptible Jailbreak",
    "Jailbroken",
    "JOOD",
    "LAA",
    "MML",
    "Mousetrap",
    "Multilingual",
    "PAIR",
    "Past Tense",
    "Prefill",
    "Query-Relevant",
    "RACE",
    "Rainbow Teaming",
    "RedQueen",
    "ReNeLLM",
    "SeqAR",
    "SI",
    "TreeAttack",
    "Visual Jailbreak",
    "X-Teaming",
}

OPENRT_METHOD_CONVERTER_COMPATIBLE = {
    "ArtPrompt": {"ascii_art"},
    "CipherChat": {"base64", "caesar", "char_code", "morse", "rot13"},
    "CodeAttack": {"code_chameleon"},
    "FigStep": {"add_text_image"},
    "FlipAttack": {"flip_text"},
    "ICA": {"few_shot"},
    "Jailbroken": {
        "composite_jailbreak",
        "dan",
        "skeleton_key",
        "template_jailbreak",
    },
    "Mousetrap": {"linguistic_confusion", "negation_trap", "prompt_injection"},
    "Multilingual": {
        "low_resource_language",
        "multilingual",
        "translation_llm",
    },
    "Past Tense": {"tense"},
    "Prefill": {"chat_inject", "prefix"},
}

OPENRT_METHOD_EXECUTOR_COMPATIBLE = {
    "Crescendo": "crescendo",
    "PAIR": "pair",
}

OPENRT_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "ASA",
    "GCG",
    "Imperceptible Jailbreak",
    "Visual Jailbreak",
}

OPENRT_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "AutoDAN",
    "AutoDAN-R",
    "AutoDAN-Turbo",
    "LAA",
    "RACE",
    "SeqAR",
}

OPENRT_REQUIRES_FUZZER_SUPPORT = {
    "GPTFuzzer",
}

OPENRT_REQUIRES_TREE_SEARCH_SUPPORT = {
    "TreeAttack",
}

OPENRT_REQUIRES_LLM_REFINEMENT_SUPPORT = {
    "CoA",
    "DrAttack",
    "RedQueen",
    "ReNeLLM",
}

OPENRT_REQUIRES_TEMPLATE_RECIPE_SUPPORT = {
    "DeepInception",
}

OPENRT_REQUIRES_MULTIMODAL_ATTACK_SUPPORT = {
    "CS-DJ",
    "HADES",
    "HIMRD",
    "IDEATOR",
    "JOOD",
    "MML",
    "Query-Relevant",
    "SI",
}

OPENRT_REQUIRES_MULTI_AGENT_ATTACK_SUPPORT = {
    "ActorAttack",
    "EvoSynth",
    "Rainbow Teaming",
    "X-Teaming",
}

FUZZYAI_CURRENT_ATTACK_INVENTORY = {
    "ActorAttack",
    "ArtPrompt",
    "ASCII smuggling",
    "BackToThePast",
    "Best-of-n jailbreaking",
    "Crescendo",
    "DAN (Do Anything Now)",
    "Default",
    "Genetic algorithm",
    "GPT Fuzzer",
    "Hallucinations",
    "History/Academic framing",
    "ManyShot",
    "PAIR - Prompt Automatic Iterative Refinement",
    "Please",
    "Shuffle Inconsistency attack",
    "Taxonomy-based paraphrasing",
    "ThoughtExperiment",
    "WordGame",
}

FUZZYAI_ATTACK_CONVERTER_COMPATIBLE = {
    "ArtPrompt": {"ascii_art"},
    "ASCII smuggling": {"ascii_smuggler"},
    "BackToThePast": {"role_prefix", "suffix", "tense"},
    "DAN (Do Anything Now)": {"dan", "template_jailbreak"},
    "Default": {"identity"},
    "History/Academic framing": {"citation_framing", "research"},
    "ManyShot": {"few_shot"},
    "Please": {"prefix", "suffix", "suffix_append", "template_jailbreak"},
    "Shuffle Inconsistency attack": {
        "llm_variation",
        "odd_even",
        "word_scramble",
    },
    "Taxonomy-based paraphrasing": {
        "emotional_manipulation",
        "llm_persuasion",
    },
    "ThoughtExperiment": {"fictional", "research", "template_jailbreak"},
    "WordGame": {"acronym", "first_letter", "nato", "word_scramble"},
}

FUZZYAI_ATTACK_EXECUTOR_COMPATIBLE = {
    "Best-of-n jailbreaking": "best_of_n",
    "Crescendo": "crescendo",
    "PAIR - Prompt Automatic Iterative Refinement": "pair",
}

FUZZYAI_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "Genetic algorithm",
}

FUZZYAI_REQUIRES_FUZZER_SUPPORT = {
    "GPT Fuzzer",
}

FUZZYAI_REQUIRES_GENERATIVE_ATTACK_SUPPORT = {
    "Hallucinations",
}

FUZZYAI_REQUIRES_MULTI_AGENT_ATTACK_SUPPORT = {
    "ActorAttack",
}

PROMPTBENCH_CURRENT_ATTACK_INVENTORY = {
    "BertAttack",
    "CheckList",
    "DeepWordBug",
    "Semantic",
    "StressTest",
    "TextBugger",
    "TextFooler",
}

PROMPTBENCH_ATTACK_CONVERTER_COMPATIBLE = {
    "BertAttack": {"llm_variation", "word_substitution"},
    "CheckList": {"context_flooding", "noise", "suffix", "suffix_append"},
    "DeepWordBug": {"char_swap", "insert_punctuation", "noise", "word_scramble"},
    "Semantic": {"llm_variation", "translation_llm"},
    "StressTest": {"context_flooding", "suffix", "suffix_append"},
    "TextBugger": {
        "char_swap",
        "insert_punctuation",
        "char_corrupt",
        "noise",
        "word_scramble",
    },
    "TextFooler": {"llm_variation", "word_substitution"},
}

TEXTATTACK_CURRENT_ATTACK_RECIPE_INVENTORY = {
    "A2T",
    "Alzantot Genetic Algorithm",
    "BAE",
    "BERT-Attack",
    "CheckList",
    "CLARE",
    "DeepWordBug",
    "Faster Alzantot Genetic Algorithm",
    "HotFlip",
    "Improved Genetic Algorithm",
    "Input Reduction",
    "Kuleshov2017",
    "MORPHEUS2020",
    "Particle Swarm Optimization",
    "Pruthi2019",
    "PWWS",
    "Seq2Sick",
    "TextBugger",
    "TextFooler",
}

TEXTATTACK_RECIPE_CONVERTER_COMPATIBLE = {
    "CheckList": {"context_flooding", "noise", "suffix", "suffix_append"},
    "DeepWordBug": {"char_swap", "insert_punctuation", "noise", "word_scramble"},
    "Kuleshov2017": {"llm_variation", "word_substitution"},
    "Pruthi2019": {"char_swap", "char_corrupt", "word_scramble"},
    "TextBugger": {
        "char_swap",
        "insert_punctuation",
        "char_corrupt",
        "noise",
        "word_scramble",
    },
    "TextFooler": {"llm_variation", "word_substitution"},
}

TEXTATTACK_REQUIRES_MODEL_GUIDED_RECIPE_SUPPORT = {
    "A2T",
    "BAE",
    "BERT-Attack",
    "CLARE",
    "Input Reduction",
    "PWWS",
}

TEXTATTACK_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "Alzantot Genetic Algorithm",
    "Faster Alzantot Genetic Algorithm",
    "Improved Genetic Algorithm",
}

TEXTATTACK_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "HotFlip",
}

TEXTATTACK_REQUIRES_PARTICLE_SWARM_OPTIMIZER_SUPPORT = {
    "Particle Swarm Optimization",
}

TEXTATTACK_REQUIRES_SEQ2SEQ_ATTACK_SUPPORT = {
    "MORPHEUS2020",
    "Seq2Sick",
}

OPENATTACK_CURRENT_ATTACKER_INVENTORY = {
    "BAEAttacker",
    "BERTAttacker",
    "DeepWordBugAttacker",
    "FDAttacker",
    "GANAttacker",
    "GEOAttacker",
    "GeneticAttacker",
    "HotFlipAttacker",
    "PSOAttacker",
    "PWWSAttacker",
    "SCPNAttacker",
    "TextBuggerAttacker",
    "TextFoolerAttacker",
    "UATAttacker",
    "VIPERAttacker",
}

OPENATTACK_ATTACKER_CONVERTER_COMPATIBLE = {
    "DeepWordBugAttacker": {
        "char_swap",
        "homoglyph",
        "insert_punctuation",
        "noise",
        "word_scramble",
    },
    "SCPNAttacker": {"llm_variation"},
    "TextBuggerAttacker": {
        "char_swap",
        "insert_punctuation",
        "char_corrupt",
        "noise",
        "word_scramble",
        "word_substitution",
    },
    "TextFoolerAttacker": {"llm_variation", "word_substitution"},
    "VIPERAttacker": {"homoglyph"},
}

OPENATTACK_REQUIRES_MODEL_GUIDED_RECIPE_SUPPORT = {
    "BAEAttacker",
    "BERTAttacker",
    "FDAttacker",
    "PWWSAttacker",
}

OPENATTACK_REQUIRES_GENETIC_OPTIMIZER_SUPPORT = {
    "GeneticAttacker",
}

OPENATTACK_REQUIRES_WHITEBOX_OPTIMIZER_SUPPORT = {
    "HotFlipAttacker",
}

OPENATTACK_REQUIRES_PARTICLE_SWARM_OPTIMIZER_SUPPORT = {
    "PSOAttacker",
}

OPENATTACK_REQUIRES_GAN_ATTACK_SUPPORT = {
    "GANAttacker",
}

OPENATTACK_REQUIRES_GEOMETRIC_ATTACK_SUPPORT = {
    "GEOAttacker",
}

OPENATTACK_REQUIRES_UNIVERSAL_TRIGGER_SUPPORT = {
    "UATAttacker",
}

OPENBACKDOOR_CURRENT_ATTACK_INVENTORY = {
    "AddSent",
    "BadNets",
    "EP",
    "LWP",
    "LWS",
    "NeuBA",
    "POR",
    "RIPPLES",
    "SOS",
    "StyleBkd",
    "SynBkd",
    "TrojanLM",
}

OPENBACKDOOR_ATTACK_CONVERTER_COMPATIBLE = {
    "AddSent": {"prefix", "suffix", "template_jailbreak"},
    "BadNets": {"prefix", "suffix", "suffix_append", "template_jailbreak"},
    "LWS": {"llm_variation", "word_substitution"},
    "StyleBkd": {"llm_tone", "llm_variation"},
    "SynBkd": {"llm_variation"},
}

OPENBACKDOOR_REQUIRES_PRETRAINED_MODEL_BACKDOOR_SUPPORT = {
    "POR",
    "TrojanLM",
}

OPENBACKDOOR_REQUIRES_WEIGHT_POISONING_SUPPORT = {
    "LWP",
    "RIPPLES",
}

OPENBACKDOOR_REQUIRES_EMBEDDING_POISONING_SUPPORT = {
    "EP",
}

OPENBACKDOOR_REQUIRES_NEURON_BACKDOOR_SUPPORT = {
    "NeuBA",
}

OPENBACKDOOR_REQUIRES_STEALTHY_BACKDOOR_TRAINING_SUPPORT = {
    "SOS",
}

BACKDOORBENCH_CURRENT_ATTACK_INVENTORY = {
    "BadNet",
    "Blended",
    "Blind",
    "Bpp",
    "CTRL",
    "InputAware",
    "LabelConsistent",
    "LIRA",
    "LowFrequency",
    "NormalCase",
    "PoisonInk",
    "Refool",
    "SIG",
    "SSBA",
    "TrojanNN",
    "Wanet",
}

BACKDOORBENCH_BASELINE_COMPATIBLE = {
    "NormalCase": "identity",
}

BACKDOORBENCH_REQUIRES_DATA_POISONING_BACKDOOR_SUPPORT = {
    "BadNet",
    "Blended",
    "Blind",
    "Bpp",
    "LabelConsistent",
    "LowFrequency",
    "PoisonInk",
    "Refool",
    "SIG",
    "SSBA",
}

BACKDOORBENCH_REQUIRES_DYNAMIC_BACKDOOR_SUPPORT = {
    "InputAware",
    "LIRA",
    "Wanet",
}

BACKDOORBENCH_REQUIRES_MODEL_MODIFICATION_BACKDOOR_SUPPORT = {
    "TrojanNN",
}

BACKDOORBENCH_REQUIRES_SELF_SUPERVISED_BACKDOOR_SUPPORT = {
    "CTRL",
}

CLEVERHANS_CURRENT_ATTACK_INVENTORY = {
    "BasicIterativeMethod",
    "BoundaryAttackPlusPlus",
    "CarliniWagnerL2",
    "DeepFool",
    "ElasticNetMethod",
    "FastFeatureAdversaries",
    "FastGradientMethod",
    "HopSkipJumpAttack",
    "LBFGS",
    "MadryEtAl",
    "MaxConfidence",
    "MomentumIterativeMethod",
    "Noise",
    "ProjectedGradientDescent",
    "SaliencyMapMethod",
    "Semantic",
    "SparseL1Descent",
    "SpatialTransformationMethod",
    "SPSA",
    "VirtualAdversarialMethod",
}

CLEVERHANS_REQUIRES_GRADIENT_EVASION_SUPPORT = {
    "BasicIterativeMethod",
    "DeepFool",
    "FastFeatureAdversaries",
    "FastGradientMethod",
    "MadryEtAl",
    "MomentumIterativeMethod",
    "ProjectedGradientDescent",
    "SaliencyMapMethod",
    "SparseL1Descent",
    "VirtualAdversarialMethod",
}

CLEVERHANS_REQUIRES_OPTIMIZATION_EVASION_SUPPORT = {
    "CarliniWagnerL2",
    "ElasticNetMethod",
    "LBFGS",
    "MaxConfidence",
}

CLEVERHANS_REQUIRES_DECISION_BASED_EVASION_SUPPORT = {
    "BoundaryAttackPlusPlus",
    "HopSkipJumpAttack",
}

CLEVERHANS_REQUIRES_GRADIENT_FREE_EVASION_SUPPORT = {
    "Noise",
    "SPSA",
}

CLEVERHANS_REQUIRES_SEMANTIC_SPATIAL_EVASION_SUPPORT = {
    "Semantic",
    "SpatialTransformationMethod",
}

FOOLBOX_CURRENT_ATTACK_INVENTORY = {
    "BinarySearchContrastReductionAttack",
    "BinarizationRefinementAttack",
    "BoundaryAttack",
    "DatasetAttack",
    "DDNAttack",
    "EADAttack",
    "FGM",
    "FGSM",
    "GaussianBlurAttack",
    "HopSkipJumpAttack",
    "InversionAttack",
    "L0BrendelBethgeAttack",
    "L0FMNAttack",
    "L1BrendelBethgeAttack",
    "L1FMNAttack",
    "L2AdditiveGaussianNoiseAttack",
    "L2AdditiveUniformNoiseAttack",
    "L2BasicIterativeAttack",
    "L2BrendelBethgeAttack",
    "L2CarliniWagnerAttack",
    "L2ClippingAwareAdditiveGaussianNoiseAttack",
    "L2ClippingAwareAdditiveUniformNoiseAttack",
    "L2ClippingAwareRepeatedAdditiveGaussianNoiseAttack",
    "L2ClippingAwareRepeatedAdditiveUniformNoiseAttack",
    "L2ContrastReductionAttack",
    "L2DeepFoolAttack",
    "L2FastGradientAttack",
    "L2FMNAttack",
    "L2PGD",
    "L2ProjectedGradientDescentAttack",
    "L2RepeatedAdditiveGaussianNoiseAttack",
    "L2RepeatedAdditiveUniformNoiseAttack",
    "LInfFMNAttack",
    "LinfAdditiveUniformNoiseAttack",
    "LinfBasicIterativeAttack",
    "LinfDeepFoolAttack",
    "LinfinityBrendelBethgeAttack",
    "LinfFastGradientAttack",
    "LinfPGD",
    "LinfProjectedGradientDescentAttack",
    "LinfRepeatedAdditiveUniformNoiseAttack",
    "LinearSearchBlendedUniformNoiseAttack",
    "LinearSearchContrastReductionAttack",
    "NewtonFoolAttack",
    "PGD",
    "PointwiseAttack",
    "SaltAndPepperNoiseAttack",
    "VirtualAdversarialAttack",
}

FOOLBOX_REQUIRES_GRADIENT_EVASION_SUPPORT = {
    "DDNAttack",
    "FGM",
    "FGSM",
    "L0BrendelBethgeAttack",
    "L0FMNAttack",
    "L1BrendelBethgeAttack",
    "L1FMNAttack",
    "L2BasicIterativeAttack",
    "L2BrendelBethgeAttack",
    "L2DeepFoolAttack",
    "L2FastGradientAttack",
    "L2FMNAttack",
    "L2PGD",
    "L2ProjectedGradientDescentAttack",
    "LInfFMNAttack",
    "LinfBasicIterativeAttack",
    "LinfDeepFoolAttack",
    "LinfinityBrendelBethgeAttack",
    "LinfFastGradientAttack",
    "LinfPGD",
    "LinfProjectedGradientDescentAttack",
    "NewtonFoolAttack",
    "PGD",
    "VirtualAdversarialAttack",
}

FOOLBOX_REQUIRES_OPTIMIZATION_EVASION_SUPPORT = {
    "EADAttack",
    "L2CarliniWagnerAttack",
}

FOOLBOX_REQUIRES_DECISION_BASED_EVASION_SUPPORT = {
    "BoundaryAttack",
    "HopSkipJumpAttack",
    "PointwiseAttack",
}

FOOLBOX_REQUIRES_NOISE_SEARCH_EVASION_SUPPORT = {
    "DatasetAttack",
    "L2AdditiveGaussianNoiseAttack",
    "L2AdditiveUniformNoiseAttack",
    "L2ClippingAwareAdditiveGaussianNoiseAttack",
    "L2ClippingAwareAdditiveUniformNoiseAttack",
    "L2ClippingAwareRepeatedAdditiveGaussianNoiseAttack",
    "L2ClippingAwareRepeatedAdditiveUniformNoiseAttack",
    "L2RepeatedAdditiveGaussianNoiseAttack",
    "L2RepeatedAdditiveUniformNoiseAttack",
    "LinfAdditiveUniformNoiseAttack",
    "LinfRepeatedAdditiveUniformNoiseAttack",
    "LinearSearchBlendedUniformNoiseAttack",
    "SaltAndPepperNoiseAttack",
}

FOOLBOX_REQUIRES_IMAGE_TRANSFORMATION_EVASION_SUPPORT = {
    "BinarySearchContrastReductionAttack",
    "GaussianBlurAttack",
    "InversionAttack",
    "L2ContrastReductionAttack",
    "LinearSearchContrastReductionAttack",
}

FOOLBOX_REQUIRES_PREPROCESSING_EVASION_SUPPORT = {
    "BinarizationRefinementAttack",
}

ART_REQUIRES_EVASION_ATTACK_SUPPORT = {
    "AdversarialPatch",
    "AdversarialPatchNumpy",
    "AdversarialPatchPyTorch",
    "AdversarialPatchTensorFlowV2",
    "AdversarialTexturePyTorch",
    "AutoAttack",
    "AutoConjugateGradient",
    "AutoProjectedGradientDescent",
    "BasicIterativeMethod",
    "BoundaryAttack",
    "BrendelBethgeAttack",
    "CarliniL0Method",
    "CarliniL2Method",
    "CarliniLInfMethod",
    "CarliniWagnerASR",
    "CompositeAdversarialAttackPyTorch",
    "DecisionTreeAttack",
    "DeepFool",
    "DPatch",
    "ElasticNet",
    "FastGradientMethod",
    "FeatureAdversariesNumpy",
    "FeatureAdversariesPyTorch",
    "FeatureAdversariesTensorFlowV2",
    "FrameSaliencyAttack",
    "GeoDA",
    "GRAPHITEBlackbox",
    "GRAPHITEWhiteboxPyTorch",
    "HighConfidenceLowUncertainty",
    "HopSkipJump",
    "ImperceptibleASR",
    "ImperceptibleASRPyTorch",
    "LaserAttack",
    "LowProFool",
    "MalwareGDTensorFlow",
    "NewtonFool",
    "OverTheAirFlickeringPyTorch",
    "PixelAttack",
    "ProjectedGradientDescent",
    "ProjectedGradientDescentNumpy",
    "ProjectedGradientDescentPyTorch",
    "ProjectedGradientDescentTensorFlowV2",
    "RobustDPatch",
    "SaliencyMapMethod",
    "ShadowAttack",
    "ShapeShifter",
    "SignOPTAttack",
    "SimBA",
    "SpatialTransformation",
    "SquareAttack",
    "TargetedUniversalPerturbation",
    "ThresholdAttack",
    "UniversalPerturbation",
    "VirtualAdversarialMethod",
    "Wasserstein",
    "ZooAttack",
}

ART_REQUIRES_POISONING_ATTACK_SUPPORT = {
    "BackdoorAttackDGMReDTensorFlowV2",
    "BackdoorAttackDGMTrailTensorFlowV2",
    "BullseyePolytopeAttackPyTorch",
    "FeatureCollisionAttack",
    "GradientMatchingAttack",
    "HiddenTriggerBackdoor",
    "PoisoningAttackAdversarialEmbedding",
    "PoisoningAttackBackdoor",
    "PoisoningAttackCleanLabelBackdoor",
    "PoisoningAttackSVM",
    "SleeperAgentAttack",
}

ART_REQUIRES_EXTRACTION_ATTACK_SUPPORT = {
    "CopycatCNN",
    "FunctionallyEquivalentExtraction",
    "KnockoffNets",
}

ART_REQUIRES_INFERENCE_PRIVACY_ATTACK_SUPPORT = {
    "AttributeInferenceBaseline",
    "AttributeInferenceBaselineTrueLabel",
    "AttributeInferenceBlackBox",
    "AttributeInferenceMembership",
    "AttributeInferenceWhiteBoxDecisionTree",
    "AttributeInferenceWhiteBoxLifestyleDecisionTree",
    "DatabaseReconstruction",
    "LabelOnlyDecisionBoundary",
    "LabelOnlyGapAttack",
    "MembershipInferenceBlackBox",
    "MembershipInferenceBlackBoxRuleBased",
    "MIFace",
    "ShadowModels",
}

ART_CURRENT_ATTACK_INVENTORY = (
    ART_REQUIRES_EVASION_ATTACK_SUPPORT
    | ART_REQUIRES_POISONING_ATTACK_SUPPORT
    | ART_REQUIRES_EXTRACTION_ATTACK_SUPPORT
    | ART_REQUIRES_INFERENCE_PRIVACY_ATTACK_SUPPORT
)

ADVERTORCH_REQUIRES_GRADIENT_EVASION_SUPPORT = {
    "DDNL2Attack",
    "FastFeatureAttack",
    "GradientAttack",
    "GradientSignAttack",
    "JacobianSaliencyMapAttack",
    "L1PGDAttack",
    "L2BasicIterativeAttack",
    "L2MomentumIterativeAttack",
    "L2PGDAttack",
    "LinfBasicIterativeAttack",
    "LinfMomentumIterativeAttack",
    "LinfPGDAttack",
    "MomentumIterativeAttack",
    "PGDAttack",
    "SparseL1DescentAttack",
}

ADVERTORCH_REQUIRES_OPTIMIZATION_EVASION_SUPPORT = {
    "CarliniWagnerL2Attack",
    "ElasticNetL1Attack",
    "LBFGSAttack",
}

ADVERTORCH_REQUIRES_SEARCH_EVASION_SUPPORT = {
    "LocalSearchAttack",
    "SinglePixelAttack",
}

ADVERTORCH_REQUIRES_SPATIAL_EVASION_SUPPORT = {
    "SpatialTransformAttack",
}

ADVERTORCH_CURRENT_ATTACK_INVENTORY = (
    ADVERTORCH_REQUIRES_GRADIENT_EVASION_SUPPORT
    | ADVERTORCH_REQUIRES_OPTIMIZATION_EVASION_SUPPORT
    | ADVERTORCH_REQUIRES_SEARCH_EVASION_SUPPORT
    | ADVERTORCH_REQUIRES_SPATIAL_EVASION_SUPPORT
)

TORCHATTACKS_BASELINE_COMPATIBLE = {
    "VANILA": "identity",
}

TORCHATTACKS_REQUIRES_GRADIENT_EVASION_SUPPORT = {
    "APGD",
    "APGDT",
    "BIM",
    "DeepFool",
    "EOTPGD",
    "FFGSM",
    "FGSM",
    "JSMA",
    "MIFGSM",
    "NIFGSM",
    "PGD",
    "PGDL2",
    "RFGSM",
    "SparseFool",
    "TPGD",
    "UPGD",
}

TORCHATTACKS_REQUIRES_INPUT_TRANSFORM_EVASION_SUPPORT = {
    "DIFGSM",
    "Jitter",
    "PIFGSM",
    "PIFGSMPP",
    "SINIFGSM",
    "TIFGSM",
    "VMIFGSM",
    "VNIFGSM",
}

TORCHATTACKS_REQUIRES_RANDOMIZED_SMOOTHING_EVASION_SUPPORT = {
    "PGDRS",
    "PGDRSL2",
}

TORCHATTACKS_REQUIRES_OPTIMIZATION_EVASION_SUPPORT = {
    "CW",
    "EADEN",
    "EADL1",
    "FAB",
}

TORCHATTACKS_REQUIRES_ATTACK_SUITE_SUPPORT = {
    "AutoAttack",
}

TORCHATTACKS_REQUIRES_SEARCH_EVASION_SUPPORT = {
    "OnePixel",
    "Pixle",
    "SPSA",
    "Square",
}

TORCHATTACKS_REQUIRES_NOISE_EVASION_SUPPORT = {
    "GN",
}

TORCHATTACKS_CURRENT_ATTACK_INVENTORY = (
    set(TORCHATTACKS_BASELINE_COMPATIBLE)
    | TORCHATTACKS_REQUIRES_ATTACK_SUITE_SUPPORT
    | TORCHATTACKS_REQUIRES_GRADIENT_EVASION_SUPPORT
    | TORCHATTACKS_REQUIRES_INPUT_TRANSFORM_EVASION_SUPPORT
    | TORCHATTACKS_REQUIRES_NOISE_EVASION_SUPPORT
    | TORCHATTACKS_REQUIRES_OPTIMIZATION_EVASION_SUPPORT
    | TORCHATTACKS_REQUIRES_RANDOMIZED_SMOOTHING_EVASION_SUPPORT
    | TORCHATTACKS_REQUIRES_SEARCH_EVASION_SUPPORT
)

SECML_REQUIRES_NATIVE_EVASION_SUPPORT = {
    "CAttackEvasionPGD",
    "CAttackEvasionPGDExp",
    "CAttackEvasionPGDLS",
}

SECML_REQUIRES_WRAPPED_FRAMEWORK_EVASION_SUPPORT = {
    "CAttackEvasionCleverhans",
    "CAttackEvasionFoolbox",
    "CFoolboxBasicIterative",
    "CFoolboxDeepfool",
    "CFoolboxEAD",
    "CFoolboxFGM",
    "CFoolboxL2CarliniWagner",
    "CFoolboxL2DDN",
    "CFoolboxPGD",
}

SECML_REQUIRES_POISONING_ATTACK_SUPPORT = {
    "CAttackPoisoningLogisticRegression",
    "CAttackPoisoningRidge",
    "CAttackPoisoningSVM",
}

SECML_CURRENT_ATTACK_INVENTORY = (
    SECML_REQUIRES_NATIVE_EVASION_SUPPORT
    | SECML_REQUIRES_WRAPPED_FRAMEWORK_EVASION_SUPPORT
    | SECML_REQUIRES_POISONING_ATTACK_SUPPORT
)

COUNTERFIT_TEXT_ATTACK_CONVERTER_COMPATIBLE = {
    "checklist_ribeiro_2020": {"context_flooding", "noise", "suffix", "suffix_append"},
    "deepwordbug_gao_2018": {"char_swap", "insert_punctuation", "noise", "word_scramble"},
    "kuleshov_2017": {"llm_variation", "word_substitution"},
    "pruthi_2019": {"char_swap", "char_corrupt", "word_scramble"},
    "textbugger_li_2018": {
        "char_swap",
        "insert_punctuation",
        "char_corrupt",
        "noise",
        "word_scramble",
    },
    "textfooler_jin_2019": {"llm_variation", "word_substitution"},
}

COUNTERFIT_REQUIRES_TEXTATTACK_RECIPE_SUPPORT = {
    "a2t_yoo_2021",
    "bae_garg_2019",
    "bert_attack_li_2020",
    "clare_li_2020",
    "faster_genetic_algorithm_jia_2019",
    "genetic_algorithm_alzantot_2018",
    "hotflip_ebrahimi_2017",
    "iga_wang_2019",
    "input_reduction_feng_2018",
    "morpheus_tan_2020",
    "pso_zang_2020",
    "pwws_ren_2019",
    "seq2sick_cheng_2018_blackbox",
}

COUNTERFIT_REQUIRES_ART_EVASION_SUPPORT = {
    "boundary",
    "carlini",
    "deepfool",
    "elastic_net",
    "hop_skip_jump",
    "newtonfool",
    "pixel_threshold",
    "projected_gradient_descent_numpy",
    "saliency_map",
    "simba",
    "spatial_transformation",
    "universal_perturbation",
    "virtual_adversarial",
    "wasserstein",
}

COUNTERFIT_REQUIRES_ART_EXTRACTION_SUPPORT = {
    "copycat_cnn",
    "functionally_equivalent_extraction",
    "knockoff_nets",
}

COUNTERFIT_REQUIRES_ART_INFERENCE_PRIVACY_SUPPORT = {
    "label_only_boundary_distance",
    "mi_face",
}

COUNTERFIT_IMAGE_TRANSFORM_CONVERTER_COMPATIBLE = {
    "EncodingQuality": {"image_compression"},
    "OverlayText": {"add_text_image"},
    "Resize": {"image_resizing"},
    "Rotate": {"image_rotation"},
    "Saturation": {"image_color_saturation"},
    "Scale": {"image_resizing"},
}

COUNTERFIT_REQUIRES_AUGLY_IMAGE_TRANSFORM_SUPPORT = {
    "ApplyLambda",
    "Blur",
    "Brightness",
    "ChangeAspectRatio",
    "ClipImageSize",
    "ColorJitter",
    "Contrast",
    "ConvertColor",
    "Crop",
    "Grayscale",
    "HFlip",
    "MemeFormat",
    "Opacity",
    "OverlayEmoji",
    "OverlayOntoScreenshot",
    "OverlayStripes",
    "Pad",
    "PadSquare",
    "PerspectiveTransform",
    "Pixelization",
    "RandomEmojiOverlay",
    "RandomNoise",
    "Sharpen",
    "ShufflePixels",
    "VFlip",
}

COUNTERFIT_CURRENT_ATTACK_INVENTORY = (
    set(COUNTERFIT_TEXT_ATTACK_CONVERTER_COMPATIBLE)
    | set(COUNTERFIT_IMAGE_TRANSFORM_CONVERTER_COMPATIBLE)
    | COUNTERFIT_REQUIRES_TEXTATTACK_RECIPE_SUPPORT
    | COUNTERFIT_REQUIRES_ART_EVASION_SUPPORT
    | COUNTERFIT_REQUIRES_ART_EXTRACTION_SUPPORT
    | COUNTERFIT_REQUIRES_ART_INFERENCE_PRIVACY_SUPPORT
    | COUNTERFIT_REQUIRES_AUGLY_IMAGE_TRANSFORM_SUPPORT
)

AZURE_AI_EVALUATION_STRATEGY_CONVERTER_COMPATIBLE = {
    "AnsiAttack": {"ansi_escape"},
    "AsciiArt": {"ascii_art"},
    "AsciiSmuggler": {"ascii_smuggler"},
    "Atbash": {"atbash"},
    "Base64": {"base64"},
    "Binary": {"binary"},
    "Caesar": {"caesar"},
    "CharacterSpace": {"character_space"},
    "CharSwap": {"char_swap"},
    "Diacritic": {"diacritic"},
    "Flip": {"flip_text"},
    "IndirectAttack": {"indirect_web_pwn"},
    "Jailbreak": {"template_jailbreak"},
    "Leetspeak": {"leetspeak"},
    "Morse": {"morse"},
    "ROT13": {"rot13"},
    "StringJoin": {"string_join"},
    "SuffixAppend": {"suffix_append"},
    "Tense": {"tense"},
    "UnicodeConfusable": {"homoglyph"},
    "UnicodeSubstitution": {"unicode_substitution"},
    "Url": {"url_encode"},
}

AZURE_AI_EVALUATION_STRATEGY_EXECUTOR_COMPATIBLE = {
    "Crescendo": "crescendo",
    "Multiturn": "jailbreak_iterative",
}

AZURE_AI_EVALUATION_GROUP_STRATEGY_COMPATIBLE = {
    "EASY": {"Base64", "Flip", "Morse"},
    "MODERATE": {"Tense"},
    "DIFFICULT": {"Base64", "Tense"},
}

AZURE_AI_EVALUATION_CURRENT_ATTACK_STRATEGY_INVENTORY = set(AZURE_AI_EVALUATION_STRATEGY_CONVERTER_COMPATIBLE) | set(
    AZURE_AI_EVALUATION_STRATEGY_EXECUTOR_COMPATIBLE
)

CYBERSECEVAL_PROMPT_INJECTION_CONVERTER_COMPATIBLE = {
    "Textual Prompt Injection Tests": {"prompt_injection"},
    "Multilingual Text Prompt Injection Tests": {"multilingual", "prompt_injection"},
    "Visual Prompt Injection Tests": {
        "add_image_text",
        "add_text_image",
        "prompt_injection",
    },
}

CYBERSECEVAL_REQUIRES_CYBER_ATTACK_HELPFULNESS_SUPPORT = {
    "MITRE Tests",
}

CYBERSECEVAL_REQUIRES_FALSE_REFUSAL_BENCHMARK_SUPPORT = {
    "MITRE False Refusal Rate Tests",
}

CYBERSECEVAL_REQUIRES_SECURE_CODE_BENCHMARK_SUPPORT = {
    "Secure Code Generation Instruct Tests",
    "Secure Code Generation Autocomplete Tests",
    "AutoPatch Tests",
}

CYBERSECEVAL_REQUIRES_CODE_INTERPRETER_ABUSE_SUPPORT = {
    "Code Interpreter Abuse Tests",
}

CYBERSECEVAL_REQUIRES_VULNERABILITY_EXPLOITATION_SUPPORT = {
    "Vulnerability Exploitation Tests",
}

CYBERSECEVAL_REQUIRES_SPEAR_PHISHING_SIMULATION_SUPPORT = {
    "Spear Phishing Capability Tests",
}

CYBERSECEVAL_REQUIRES_AUTONOMOUS_CYBER_RANGE_SUPPORT = {
    "Autonomous Offensive Cyber Operations Tests",
}

CYBERSECEVAL_REQUIRES_DEFENSIVE_CYBER_REASONING_SUPPORT = {
    "Malware Analysis Tests",
    "Threat Intelligence Reasoning Tests",
}

CYBERSECEVAL_CURRENT_BENCHMARK_INVENTORY = (
    set(CYBERSECEVAL_PROMPT_INJECTION_CONVERTER_COMPATIBLE)
    | CYBERSECEVAL_REQUIRES_CYBER_ATTACK_HELPFULNESS_SUPPORT
    | CYBERSECEVAL_REQUIRES_FALSE_REFUSAL_BENCHMARK_SUPPORT
    | CYBERSECEVAL_REQUIRES_SECURE_CODE_BENCHMARK_SUPPORT
    | CYBERSECEVAL_REQUIRES_CODE_INTERPRETER_ABUSE_SUPPORT
    | CYBERSECEVAL_REQUIRES_VULNERABILITY_EXPLOITATION_SUPPORT
    | CYBERSECEVAL_REQUIRES_SPEAR_PHISHING_SIMULATION_SUPPORT
    | CYBERSECEVAL_REQUIRES_AUTONOMOUS_CYBER_RANGE_SUPPORT
    | CYBERSECEVAL_REQUIRES_DEFENSIVE_CYBER_REASONING_SUPPORT
)

SPIKEE_JAILBREAK_CONVERTER_COMPATIBLE = {
    "academic": {"research", "template_jailbreak"},
    "challenge": {"template_jailbreak"},
    "dan": {"dan", "template_jailbreak"},
    "debug": {"template_jailbreak"},
    "dev": {"template_jailbreak"},
    "emergency": {"template_jailbreak"},
    "errors": {"template_jailbreak"},
    "experimental": {"template_jailbreak"},
    "hidden-function": {"prompt_probing", "template_jailbreak"},
    "ignore": {"prompt_injection"},
    "new-instructions": {"prompt_injection", "system_override"},
    "new-task": {"goal_redirection", "template_jailbreak"},
    "no-limits": {"template_jailbreak"},
    "sorry": {"template_jailbreak"},
    "test": {"template_jailbreak"},
    "training": {"template_jailbreak"},
}

SPIKEE_INSTRUCTION_CONVERTER_COMPATIBLE = {
    "long-output": {"context_flooding", "repeat_token"},
    "translation_llm": {"translation_llm"},
}

SPIKEE_EVASION_PLUGIN_CONVERTER_COMPATIBLE = {
    "1337": {"leetspeak"},
    "ascii_smuggler": {"ascii_smuggler"},
    "base64": {"base64"},
    "best_of_n": {"random_case", "word_scramble"},
    "caesar": {"caesar"},
    "hex": {"hex"},
    "morse": {"morse"},
    "prompt_decomposition_*": {"payload_split"},
    "splat": {"character_space", "insert_punctuation", "noise"},
}

SPIKEE_EVASION_PLUGIN_EXECUTOR_COMPATIBLE = {
    "best_of_n": "best_of_n",
}

SPIKEE_REQUIRES_APPLICATION_OUTCOME_SUPPORT = {
    "data-exfil-markdown",
    "encoding",
    "xss",
}

SPIKEE_REQUIRES_SPOTLIGHTING_BYPASS_SUPPORT = {
    "anti_spotlighting",
}

SPIKEE_CURRENT_ATTACK_METHOD_INVENTORY = (
    set(SPIKEE_JAILBREAK_CONVERTER_COMPATIBLE)
    | set(SPIKEE_INSTRUCTION_CONVERTER_COMPATIBLE)
    | set(SPIKEE_EVASION_PLUGIN_CONVERTER_COMPATIBLE)
    | set(SPIKEE_EVASION_PLUGIN_EXECUTOR_COMPATIBLE)
    | SPIKEE_REQUIRES_APPLICATION_OUTCOME_SUPPORT
    | SPIKEE_REQUIRES_SPOTLIGHTING_BYPASS_SUPPORT
)

OPEN_PROMPT_INJECTION_ATTACKER_CONVERTER_COMPATIBLE = {
    "combine": {
        "composite_jailbreak",
        "deepset_injection_dataset",
        "prompt_injection",
        "suffix_append",
    },
    "escape": {"suffix_append", "template_segment"},
    "fake_comp": {"deepset_injection_dataset", "template_jailbreak"},
    "ignore": {"deepset_injection_dataset", "prefix", "prompt_injection"},
    "naive": {"prompt_injection", "suffix_append"},
}

OPEN_PROMPT_INJECTION_CURRENT_ATTACKER_INVENTORY = set(OPEN_PROMPT_INJECTION_ATTACKER_CONVERTER_COMPATIBLE)

BIPIA_TEXT_ATTACK_CONVERTER_COMPATIBLE = {
    "Base Encoding": {"base64", "hex"},
    "Emoji Substitution": {"emoji_substitution"},
    "Language Translation": {"multilingual", "translation_llm"},
    "Reverse Text": {"flip_text"},
    "Substitution Ciphers": {"caesar"},
}

BIPIA_REQUIRES_APPLICATION_GOAL_INJECTION_SUPPORT = {
    "Business Intelligence",
    "Conversational Agent",
    "Research Assistance",
    "Sentiment Analysis",
    "Task Automation",
}

BIPIA_REQUIRES_CONTENT_OUTCOME_SUPPORT = {
    "Entertainment",
    "Information Dissemination",
    "Marketing & Advertising",
    "Misinformation & Propaganda",
    "Scams & Fraud",
}

BIPIA_REQUIRES_CODE_ABUSE_BENCHMARK_SUPPORT = {
    "Blocking Internet Connection",
    "Bringing Down Hosts and Servers (Denial of Service)",
    "Compromising Computers",
    "Corrupting an Operating System",
    "Data Eavesdropping",
    "Encrypting Documents and Demanding Ransom (Ransomware)",
    "Introduce System Fingerprinting",
    "Keylogging",
    "Screen Scraping",
    "Traffic Analysis",
}

BIPIA_CURRENT_ATTACK_CATEGORY_INVENTORY = (
    set(BIPIA_TEXT_ATTACK_CONVERTER_COMPATIBLE)
    | BIPIA_REQUIRES_APPLICATION_GOAL_INJECTION_SUPPORT
    | BIPIA_REQUIRES_CONTENT_OUTCOME_SUPPORT
    | BIPIA_REQUIRES_CODE_ABUSE_BENCHMARK_SUPPORT
)

MOONSHOT_ATTACK_MODULE_CONVERTER_COMPATIBLE = {
    "Character Swap Attack": {"char_swap"},
    "Colloquial Wordswap": {"colloquial_wordswap"},
    "Homoglyph Attack": {"homoglyph"},
    "Homoglyph V2 Attack": {"homoglyph"},
    "Insert Punctuation Attack": {"insert_punctuation"},
    "Job Role Generator Module": {"job_role_generator"},
    "Malicious Question Generator": {"llm_malicious_question"},
    "Payload Mask Attack": {"payload_mask_attack"},
    "Singapore Sentence Generator": {"sg_sentence_generator"},
    "TextBugger Attack": {
        "char_swap",
        "insert_punctuation",
        "char_corrupt",
        "noise",
        "word_scramble",
    },
    "TextFooler Attack": {"llm_variation", "word_substitution"},
    "Toxic Sentence Generator": {"llm_toxic_sentence"},
}

MOONSHOT_REQUIRES_MULTI_TURN_AGENT_SUPPORT = {
    "Violent Durian",
}

MOONSHOT_CURRENT_ATTACK_MODULE_INVENTORY = (
    set(MOONSHOT_ATTACK_MODULE_CONVERTER_COMPATIBLE) | MOONSHOT_REQUIRES_MULTI_TURN_AGENT_SUPPORT
)

DEEPTEAM_TEXT_COMPATIBLE = {
    "adversarial_poetry",
    "authority_escalation",
    "base64",
    "character_stream",
    "context_flooding",
    "context_poisoning",
    "embedded_instruction_json",
    "emotional_manipulation",
    "goal_redirection",
    "gray_box",
    "input_bypass",
    "leetspeak",
    "linguistic_confusion",
    "math_prompt",
    "multilingual",
    "permission_escalation",
    "prompt_probing",
    "rot13",
    "prompt_injection",
    "roleplay",
    "semantic_manipulation",
    "synthetic_context_injection",
    "system_override",
    "translation_llm",
}

DEEPTEAM_CURRENT_SINGLE_TURN_ATTACK_INVENTORY = {
    "adversarial_poetry",
    "authority_escalation",
    "base64",
    "character_stream",
    "context_flooding",
    "context_poisoning",
    "embedded_instruction_json",
    "emotional_manipulation",
    "goal_redirection",
    "gray_box",
    "input_bypass",
    "leetspeak",
    "math_prompt",
    "multilingual",
    "permission_escalation",
    "prompt_injection",
    "prompt_probing",
    "roleplay",
    "rot13",
    "semantic_manipulation",
    "synthetic_context_injection",
    "system_override",
}

DEEPTEAM_CURRENT_MULTI_TURN_ATTACK_INVENTORY = {
    "bad_likert_judge",
    "crescendo_jailbreaking",
    "linear_jailbreaking",
    "sequential_break",
    "tree_jailbreaking",
}

DEEPTEAM_REQUIRES_MULTI_TURN_ATTACK_SUPPORT = {
    "bad_likert_judge",
    "crescendo_jailbreaking",
    "linear_jailbreaking",
    "sequential_break",
    "tree_jailbreaking",
}
