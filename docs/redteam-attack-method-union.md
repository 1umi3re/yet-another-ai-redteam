# Red-Team Benchmark Coverage And Converter Suite

This document is the human-readable coverage sheet for investigated red-team benchmarks/frameworks and the current canonical AiredTeam converter suite.

Source of truth: `airedteam/builtins/converters/frameworks/coverage.py` for upstream framework inventories and `pyproject.toml` for registered converter entry points.

Policy: upstream benchmark method names stay in source spelling; local converter rows use strict canonical converter IDs only. Alias and compatibility converter IDs are intentionally not listed as current converters.

## Sheet 1 - Investigated Benchmarks And Frameworks

| Benchmark / framework | Investigated upstream inventory | Local coverage summary |
| --- | --- | --- |
| PyRIT | converter inventory: `add_image_text`, `add_image_to_video`, `add_text_image`, `ansi_escape`, `ascii_art`, `ascii_smuggler`, `ask_to_decode`, `atbash`, `audio_echo`, `audio_frequency`, `audio_speed`, `audio_volume`, `audio_white_noise`, `azure_speech_audio_to_text`, `azure_speech_text_to_audio`, `base2048`, `base64`, `bin_ascii`, `binary`, `braille`, `caesar`, `char_swap`, `character_space`, `code_chameleon`, `colloquial_wordswap`, `denylist`, `diacritic`, `ecoji`, `emoji_substitution`, `first_letter`, `flip_text`, `homoglyph`, `image_color_saturation`, `image_compression`, `image_resizing`, `image_rotation`, `insert_punctuation`, `json_string`, `leetspeak`, `llm_generic`, `llm_malicious_question`, `llm_persuasion`, `llm_random_translation`, `llm_scientific_translation`, `llm_tone`, `llm_toxic_sentence`, `llm_variation`, `math_obfuscation`, `math_prompt`, `morse`, `nato`, `negation_trap`, `noise`, `pdf`, `qr_code`, `random_case`, `repeat_token`, `rot13`, `search_replace`, `selective_text`, `sneaky_bits_smuggler`, `string_join`, `suffix_append`, `superscript`, `template_jailbreak`, `template_segment`, `tense`, `translation_llm`, `transparency_attack`, `unicode_replacement`, `unicode_substitution`, `url_encode`, `variation_selector_smuggler`, `word_doc`, `zalgo`, `zero_width`<br>text selection strategy inventory: `all_words_selection_strategy`, `index_selection_strategy`, `keyword_selection_strategy`, `position_selection_strategy`, `proportion_selection_strategy`, `range_selection_strategy`, `regex_selection_strategy`, `text_selection_strategy`, `token_selection_strategy`, `word_index_selection_strategy`, `word_keyword_selection_strategy`, `word_position_selection_strategy`, `word_proportion_selection_strategy`, `word_regex_selection_strategy`, `word_selection_strategy` | Converters: 92 mapped |
| garak | buff inventory: `base64`, `char_code`, `low_resource_language`, `lowercase`, `paraphrase_fast`, `paraphrase_pegasus` | Converters: 8 mapped |
| AegisRT | converter inventory: `acronym`, `base64`, `caesar`, `case_swap`, `character_space`, `few_shot`, `fictional`, `flip_text`, `hex`, `homoglyph`, `instruction_tag`, `leetspeak`, `llm_variation`, `markdown_wrapper`, `morse`, `payload_split`, `pig_latin`, `research`, `role_prefix`, `rot13`, `sandwich`, `suffix`, `translation_llm`, `url_encode`, `whitespace`, `word_substitution`, `zero_width` | Converters: 27 mapped |
| EasyJailbreak | attacker recipe inventory: `autodan`, `cipher`, `code_chameleon`, `deepinception`, `gcg`, `gptfuzzer`, `ica`, `jailbroken`, `mjp`, `multilingual`, `pair`, `renellm`, `tap`<br>generation mutator inventory: `apply_gpt_mutation`, `char_corrupt`, `crossover`, `historical_insight`, `introspect_generation`, `llm_tone`, `llm_variation`, `noise`, `translation_llm`<br>rule mutator inventory: `artificial`, `ascii_expert`, `auto_obfuscation`, `auto_payload_splitting`, `base64`, `base64_input_only`, `base64_raw`, `binary_tree`, `caser_expert`, `combination_1`, `combination_2`, `combination_3`, `crossover`, `disemvowel`, `flip_text`, `inception`, `leetspeak`, `length`, `mjp_choices`, `morse_expert`, `odd_even`, `replace_words_with_synonyms`, `rot13`, `self_define_cipher`, `translate` | Converters: 21 mapped<br>Executors: `pair`<br>Non-converter support tracked: 15 items |
| Promptfoo | strategy inventory: `add_image_to_video`, `add_text_image`, `authoritative_markup`, `azure_speech_text_to_audio`, `base64`, `basic`, `best_of_n`, `camel_case`, `citation_framing`, `composite_jailbreak`, `crescendo`, `custom`, `custom_script`, `emoji_smuggling`, `gcg`, `goat`, `hex`, `homoglyph`, `hydra`, `indirect_web_pwn`, `jailbreak_iterative`, `layer`, `leetspeak`, `likert_framing`, `math_prompt`, `meta_agent`, `mischievous_user`, `morse`, `pig_latin`, `retry_regression`, `rot13`, `template_jailbreak`, `tree_based` | Converters: 27 mapped<br>Executors: `best_of_n`, `crescendo`, `jailbreak_iterative`<br>Non-converter support tracked: 6 items |
| DeepTeam | multi turn attack inventory: `bad_likert_judge`, `crescendo_jailbreaking`, `linear_jailbreaking`, `sequential_break`, `tree_jailbreaking`<br>single turn attack inventory: `adversarial_poetry`, `authority_escalation`, `base64`, `character_stream`, `context_flooding`, `context_poisoning`, `embedded_instruction_json`, `emotional_manipulation`, `goal_redirection`, `gray_box`, `input_bypass`, `leetspeak`, `math_prompt`, `multilingual`, `permission_escalation`, `prompt_injection`, `prompt_probing`, `roleplay`, `rot13`, `semantic_manipulation`, `synthetic_context_injection`, `system_override` | Converters: 24 mapped<br>Non-converter support tracked: 5 items |
| Giskard | prompt injection converter inventory: `ascii_smuggling`, `base64`, `chat_inject`, `citation_framing`, `control_chars_injection`, `control_chars_repetition`, `dan`, `deepset_injection_dataset`, `grandma_framing`, `likert_framing`, `math_prompt`, `nato`, `random_case`, `token_break`, `transliteration`, `word_scramble` | Converters: 17 mapped<br>Non-converter support tracked: 1 items |
| AgentDojo | attack inventory: `captcha_dos`, `direct`, `dos`, `felony_dos`, `ignore_previous`, `important_instructions`, `important_instructions_no_model_name`, `important_instructions_no_names`, `important_instructions_no_user_name`, `important_instructions_wrong_model_name`, `important_instructions_wrong_user_name`, `injecagent`, `manual`, `offensive_email_dos`, `swearwords_dos`, `system_message`, `tool_knowledge` | Converters: 6 mapped<br>Non-converter support tracked: 7 items |
| Inspect Evals AgentDojo | attack inventory: `important_instructions` | Converters: 3 mapped |
| AgentHarm | attack method inventory: `Benign Counterpart Tasks`, `Chat Dataset`, `Detailed Tasks`, `Direct Prompting Attacks`, `Hint Included Tasks`, `Open Ended Tasks`, `Simple Universal Jailbreak Templates`<br>harm category inventory: `Copyright`, `Cybercrime`, `Disinformation`, `Drugs`, `Fraud`, `Harassment`, `Hate`, `Self-harm`, `Sexual`, `Terrorism`, `Violence` | Converters: 2 mapped<br>Non-converter support tracked: 16 items |
| SafeArena | attack method inventory: `Direct Prompting`, `Priming`, `Task Decomposition Attack`<br>harm category inventory: `Bias`, `Cybercrime`, `Harassment`, `Illegal Activity`, `Misinformation` | Converters: 3 mapped<br>Non-converter support tracked: 6 items |
| OS-Harm | attack method inventory: `Direct Request`, `Jailbreak Template`, `Prompt Injection Attacks`<br>harm vector inventory: `Deliberate User Misuse`, `Model Misbehavior`, `Prompt Injection Attacks`<br>injection goal inventory: `Delete All System Files`, `Delete All User Documents`, `Leak Password via URL`, `Run Local Shell Script`, `Run Remote Shell Script`, `Send Files over Email`, `Send Files over SwissTransfer`, `Send Password over Email`, `Send SSH Keys over Web Form`, `Send User Prompt over Email`, `Set up CRON Job`, `Stop Task`<br>injection vector inventory: `Code Comments in VS Code`, `Desktop Notification`, `Document in LibreOffice Writer`, `Mail Draft in Thunderbird`, `Mail Received in Thunderbird`, `Website in Chrome`<br>misuse category inventory: `Copyright Infringement`, `Cybercrime`, `Disinformation`, `Fraud`, `Harassment` | Converters: 3 mapped<br>Non-converter support tracked: 26 items |
| Agent Security Bench | attack mode inventory: `Direct Prompt Injection`, `Memory Poisoning`, `Mixed Attack`, `Observation Prompt Injection`, `Plan-of-Thought Backdoor`<br>prompt injection payload inventory: `combined_attack`, `context_ignoring`, `escape_characters`, `fake_completion`, `naive` | Converters: 7 mapped<br>Non-converter support tracked: 5 items |
| InjecAgent | attack method inventory: `Data Stealing Attack`, `Direct Harm Attack`, `Enhanced Hacking Prompt`, `Indirect Prompt Injection`<br>data stealing category inventory: `Financial Data`, `Others`, `Physical Data`<br>data stealing stage inventory: `Data Extraction`, `Data Transmission`<br>direct harm category inventory: `Data Security Harm`, `Financial Harm`, `Physical Harm` | Converters: 4 mapped<br>Non-converter support tracked: 10 items |
| AgentVigil | attack method inventory: `ASR Seed Scoring`, `Adaptive Seed Optimization`, `AgentDojo Injection Tasks`, `Arbitrary URL Navigation`, `Coverage Bonus Seed Scoring`, `Crossover`, `Delimiter-based Seed Templates`, `Expand`, `GenerateSimilar`, `Goal Misdirection`, `High-quality Initial Seed Corpus`, `Illusioning`, `Indirect Prompt Injection`, `MCTS Seed Selection`, `Prompt Obfuscation Seed Templates`, `Rephrase`, `Role-playing Seed Templates`, `Shorten`, `VWA-adv Text Trigger Tasks` | Converters: 9 mapped<br>Non-converter support tracked: 11 items |
| VisualWebArena-Adv | attack goal inventory: `Comment`, `Comments`, `Different Object`, `Email`, `Forum`, `Homepage`, `Illusioning`, `Language`, `Login`, `Message`, `Newsletter`, `Order Attribute`, `Post`, `Post Title`, `Product Attribute`, `Reply`, `Review`, `Shopping Cart`, `Social Media Comment`, `Social Media Post`, `Sort By`, `URL`, `User Attribute`<br>attack method inventory: `Adversarial Information Flow Decomposition`, `Agent Robustness Evaluation`, `Black-box Image Attack`, `Black-box Prompt Injection Attack`, `CLIP Attack`, `CLIP Attack on Base Agents`, `CLIP Attack on Self-captioning Agents`, `CLIP Ensemble Attack`, `Captioner Attack`, `Execution-based Evaluation`, `Goal Misdirection`, `Low-resolution Perturbation Optimization`, `Negative Text Optimization`, `PGD Image Perturbation`, `Policy + Evaluator Attack`, `Policy + Value Function Attack`, `Policy Attack`, `Trigger Image`, `Trigger Text`, `Value Function Attack`, `VisualWebArena Adversarial Tasks`, `White-box Image Attack` | Converters: 3 mapped<br>Non-converter support tracked: 19 items |
| UDora | attack method inventory: `Adversarial String Optimization`, `AgentHarm Function Triggering Attack`, `Dynamic Position Identification`, `Dynamic Reasoning Hijacking`, `InjecAgent Indirect Prompt Injection Attack`, `Joint Optimization`, `Malicious Environment`, `Malicious Instruction`, `Minimize Reward`, `Multi-Noise Surrogate Optimization`, `Multi-Potential Targets for Attack on One Instance`, `Positional Scoring`, `Prompt Injection Optimization (beta)`, `Readable Attack`, `Reasoning Trace Collection`, `Self-Response Hijacking`, `Sequential Optimization`, `UDora (All)`, `UDora (Joint)`, `UDora (Sequential)`, `WebShop E-commerce Agent Attack`, `Weighted Interval Scheduling Algorithm`<br>injecagent attack type inventory: `Data Stealing`, `Direct Harm`<br>webshop attack goal inventory: `All Mismatch`, `Attribute Mismatch`, `Category Mismatch`, `Price Mismatch` | Converters: 4 mapped<br>Non-converter support tracked: 20 items |
| ARMs | adversarial pattern inventory: `Typographic transformation`, `Visual context cloaking`, `Visual multi-turn escalation`, `Visual perturbation`, `Visual reasoning hijacking`<br>attack strategy inventory: `Acronym`, `Actor attack`, `Crescendo`, `Email thread`, `Flowchart`, `Jigsaw scramble`, `Many-shot mixup`, `Multimodal shuffling`, `Multimodal trigger backdoor`, `Narrative`, `News report`, `Numbered-list image`, `Photographic`, `Rule-based`, `Scenario playing`, `Simulated function-call`, `Slack conversation`<br>framework mechanism inventory: `ARMs-Bench`, `Epsilon-greedy Attack Exploration`, `Layered Memory`, `Plug-and-Play MCP Attack Strategy Library`, `Policy-based Safety Evaluation`, `Reasoning-enhanced Multi-step Orchestration` | Converters: 10 mapped<br>Executors: `crescendo`<br>Non-converter support tracked: 17 items |
| X-Teaming | attack method inventory: `Adaptive Attack Execution and Optimization`, `Context`, `Guard-Train`, `Harmfulness Score Verification`, `Multi-turn Jailbreaks`, `Overall attack strategy`, `Persona definition`, `Plan Extension`, `Strategic Attack Planning`, `TextGrad Prompt Optimization`, `Textual Gradient Descent`, `Turn-level Progression Plans`, `Verifier-guided Query Refinement`, `XGuard-Train`<br>framework component inventory: `Attacker`, `Planner`, `Prompt Optimizer`, `Verifier` | Converters: 7 mapped<br>Executors: `jailbreak_iterative`<br>Non-converter support tracked: 10 items |
| AutoRedTeamer | attack method inventory: `Aegis2.0 Training`, `ArtPrompt`, `Attack Advancement`, `Attack Designer`, `Attack Judge`, `Attack Library`, `Attack Memory`, `Authority Manipulation`, `AutoRedTeamer Data`, `Cultural References`, `Emotional Manipulation`, `FewShot`, `Historical Scenarios`, `HumanJailbreaks`, `Jailbreak Indicators`, `Lifelong Attack Integration`, `PAIR`, `PAIR+Rephrase`, `Past Tense`, `Reasoning Puzzles`, `Red Teaming Agent`, `Reframe`, `Relevance Check`, `Risk Analyzer`, `Role Play`, `Seed Prompt Generator`, `Strategy Designer`, `Strategy Evolution`, `Strategy Proposer Agent`, `Technical Slang`, `Uncommon Dialects`, `Universal Pliny Prompt`, `Word Play` | Converters: 27 mapped<br>Executors: `pair`<br>Non-converter support tracked: 15 items |
| LLAMATOR | attack method inventory: `Adversarial Suffix`, `Aim Jailbreak`, `AutoDAN-Turbo`, `Base64 Injection`, `Best-of-N (BoN) Jailbreak`, `Composition of Principles (CoP)`, `Crescendo`, `Deceptive Delight`, `Dialogue Injection: Continuation`, `Dialogue Injection: Developer mode`, `Do Anything Now (DAN) Jailbreak`, `Ethical Compliance`, `HarmBench`, `Linguistic Evasion`, `Linguistic Sandwich`, `Logical Inconsistencies Test`, `Lowres Documents Hallucination Attack`, `M-Attack`, `Prompt Automatic Iterative Refinement (PAIR)`, `Repetition Token`, `Semantic Game`, `Shuffle Inconsistency`, `Sycophancy Test`, `System Prompt Leakage`, `Text Hallucination Attack`, `Time Machine`, `UCAR Jailbreak` | Converters: 33 mapped<br>Executors: `best_of_n`, `crescendo`, `pair`<br>Non-converter support tracked: 2 items |
| HarmBench | method inventory: `ArtPrompt`, `AutoDAN`, `AutoPrompt`, `DirectRequest`, `EnsembleGCG`, `FewShot`, `GBDA`, `GCG`, `GPTFuzz`, `HumanJailbreaks`, `MultiModalDirectRequest`, `MultiModalPGD`, `MultiModalPGDBlankImage`, `MultiModalPGDPatch`, `MultiModalRenderText`, `PAIR`, `PAP`, `PEZ`, `TAP`, `UAT`, `ZeroShot` | Converters: 6 mapped<br>Executors: `pair`<br>Non-converter support tracked: 14 items |
| JailbreakBench | artifact method inventory: `DSN`, `GCG`, `JBC`, `PAIR`, `prompt_with_random_search` | Converters: 2 mapped<br>Executors: `pair`<br>Non-converter support tracked: 3 items |
| JailTrickBench | attack method inventory: `AdvPrompter`, `AmpleGCG`, `AutoDAN`, `DrAttack`, `GCG`, `GPTFuzz`, `MultiJail`, `PAIR`, `TAP` | Converters: 3 mapped<br>Executors: `pair`<br>Non-converter support tracked: 7 items |
| PandaGuard | attack method inventory: `ArtPrompt`, `AutoDAN`, `Cold Attack`, `DeepInception`, `GCG`, `GPT4-Cipher`, `GPTFuzzer`, `ICA`, `Overload Attack`, `PAIR`, `RandomSearch`, `ReNeLLM`, `Rewrite Attack`, `SCAV`, `TAP`, `Transfer-based Attacks` | Converters: 14 mapped<br>Executors: `pair`<br>Non-converter support tracked: 9 items |
| AISafetyLab | attack method inventory: `AdvPrompter`, `AutoDAN`, `Cipher`, `DeepInception`, `GCG`, `GPTFUZZER`, `In-Context-Learning Attack`, `Jailbroken`, `LAA`, `Multilingual`, `PAIR`, `ReNeLLM`, `TAP` | Converters: 16 mapped<br>Executors: `pair`<br>Non-converter support tracked: 8 items |
| StrongREJECT | jailbreak inventory: `aim`, `auto_obfuscation`, `auto_payload_splitting`, `base64`, `base64_input_only`, `base64_output_only`, `base64_raw`, `bon`, `combination_2`, `combination_3`, `dev_mode_v2`, `dev_mode_with_rant`, `disemvowel`, `distractors`, `distractors_negated`, `evil_confidant`, `few_shot_json`, `gcg_transfer_harmbench`, `gcg_transfer_universal_attacks`, `none`, `pair`, `pap_authority_endorsement`, `pap_evidence_based_persuasion`, `pap_expert_endorsement`, `pap_logical_appeal`, `pap_misrepresentation`, `poems`, `prefix_injection`, `refusal_suppression`, `renellm`, `rot_13`, `style_injection_json`, `style_injection_short`, `translation_guarani`, `translation_hmong`, `translation_scotts_gaelic`, `translation_zulu`, `wikipedia`, `wikipedia_with_title` | Converters: 31 mapped<br>Executors: `pair`<br>Non-converter support tracked: 2 items |
| GuidedBench | evaluated method inventory: `AutoDAN`, `DRA`, `DeepInception`, `FSJ`, `GCG`, `GPTFuzzer`, `MultiJail`, `SCAV`<br>survey method inventory: `ASETF`, `Adaptive`, `AdvPrompter`, `AmpleGCG`, `AutoDAN`, `AutoDAN-turbo`, `CPAD`, `CipherChat`, `CodeAttack`, `CodeChameleon`, `DAN`, `DRA`, `Decoding`, `DeepInception`, `Drattack`, `FSJ`, `FuzzLLM`, `GA`, `GCG`, `GPTFuzzer`, `GUARD`, `ICA`, `JRE`, `LACE`, `MultiJail`, `PAIR`, `PAL`, `PRP`, `Persona Modulation`, `Query`, `ReNeLLM`, `SAP`, `SCAV`, `SMJ`, `TASTLE` | Converters: 14 mapped<br>Executors: `pair`<br>Non-converter support tracked: 26 items |
| AutoDAN | attack inventory: `AutoDAN-GA`, `AutoDAN-HGA`, `AutoDAN-HGA with GPT mutation` | Non-converter support tracked: 3 items |
| AI-Infra-Guard | attack method inventory: `A1Z26`, `AffineCipher`, `AsciiSmuggling`, `Aurebesh`, `Caesar`, `Crescendo`, `Leetspeak`, `MirrorText`, `Ogham`, `Stego`, `StrataSword suite`, `TAP`, `Vaporwave`, `Zalgo` | Converters: 14 mapped<br>Executors: `crescendo`<br>Non-converter support tracked: 2 items |
| JailbreakLLM | attack vector inventory: `API System Injection`, `ASCII Obfuscation`, `Bad Likert Judge`, `Chaos Chain (Reasoning Models)`, `Crescendo`, `Cyber-Ops Role-play`, `DarkForge-X Cyber Ops`, `Deceptive Delight`, `Direct Request (Professional Frame)`, `Dual Intention Escape`, `First-Person Confessional`, `Function Smuggling`, `GCG Override`, `Gaybreak Persona`, `Grammar Hijack (vLLM/SGLang)`, `InfoFlood Overload`, `Investigator Agent`, `Knowledge Decomposition (KDA)`, `Love Pliny Divider`, `Many-Shot Decomposition`, `Multi-turn Escalation`, `Multilingual Trojan`, `Policy Audit Mode`, `Prefix Injection`, `Prompt Fuzzing`, `Qwen Liberation Prompt`, `Raw Override Mode`, `Reason Step-by-Step`, `SIGMA-PROTOCOL`, `Screenplay Deception`, `Shadow Mode V99`, `ShadowHacker-GOD`, `Speculative Preservation`, `Storyteller Trend`, `System Policy Override`, `Token Manipulation`, `TombRaider Archive`, `Universal Divider / LSD`, `XBreaking Interpretability` | Converters: 43 mapped<br>Executors: `crescendo`, `jailbreak_iterative`<br>Non-converter support tracked: 6 items |
| h4rm3l | baseline attack inventory: `handcrafted_02`, `handcrafted_03`, `handcrafted_04`, `handcrafted_05`, `handcrafted_06_persuasion`, `sota_AIM`, `sota_DAN`, `sota_PAP`, `sota_aff_prfx_inj`, `sota_b64`, `sota_cipher`, `sota_combination_3`, `sota_cot`, `sota_few_shots`, `sota_lr_translation`, `sota_obf_pyld_splitting`, `sota_ref_suppr`, `sota_style_short`, `sota_uta_bard`, `sota_uta_gpt`, `sota_uta_llama`, `sota_wikipedia`<br>primitive inventory: `AIMDecorator`, `AffirmativePrefixInjectionDecorator`, `AnswerStyleDecorator`, `Base64Decorator`, `ChainofThoughtDecorator`, `CharCorrupt`, `CharDropout`, `CipherDecorator`, `ColorMixInDecorator`, `DANDecorator`, `DialogStyleDecorator`, `DistractorDecorator`, `FewShotDecorator`, `HexStringMixInDecorator`, `JekyllHydeDialogStyleDecorator`, `MilitaryWordsMixInDecorator`, `PAPDecorator`, `PayloadSplittingDecorator`, `PersuasiveDecorator`, `QuestionIdentificationDecorator`, `RefusalSuppressionDecorator`, `ResearcherDecorator`, `RoleplayingDecorator`, `StyleInjectionJSONDecorator`, `StyleInjectionShortDecorator`, `SynonymDecorator`, `TemplateDecorator`, `TransformFxDecorator`, `TranslateBackDecorator`, `TranslateDecorator`, `UTADecorator`, `VillainDecorator`, `WikipediaDecorator`, `WordMixInDecorator`<br>synthesis method inventory: `ASR Rewarded Bandits`, `Offspring ASR Rewarded Bandits`, `Random Bandits` | Converters: 31 mapped<br>Non-converter support tracked: 4 items |
| GPTFuzzer | fuzzing component inventory: `Fine-tuned RoBERTa judgment model`, `GPTFuzzer fuzzing loop`, `Human-written jailbreak seed templates`<br>mutator inventory: `OpenAIMutatorCrossOver`, `OpenAIMutatorExpand`, `OpenAIMutatorGenerateSimilar`, `OpenAIMutatorRephrase`, `OpenAIMutatorShorten`<br>selection policy inventory: `EXP3SelectPolicy`, `MCTSExploreSelectPolicy`, `RandomSelectPolicy`, `RoundRobinSelectPolicy`, `UCBSelectPolicy` | Converters: 1 mapped<br>Non-converter support tracked: 9 items |
| RaccoonBench | singular attack inventory: `Cognitive Hacking`, `Context Ignoring Attack`, `Context Manipulation Attack`, `Defined Dictionary Attack`, `Distractor Instructions Attack`, `Few Shot Prompt`, `Fill in the Blank Attack`, `Instruction Repetition Attack`, `Obfuscation`, `Payload Splitting`, `Plain`, `Prefix Injection Attack`, `Refusal Suppression Attack`, `Special Case Attack`, `Translation` | Converters: 23 mapped |
| OpenRT | attack method inventory: `ASA`, `ActorAttack`, `ArtPrompt`, `AutoDAN`, `AutoDAN-R`, `AutoDAN-Turbo`, `CS-DJ`, `CipherChat`, `CoA`, `CodeAttack`, `Crescendo`, `DeepInception`, `DrAttack`, `EvoSynth`, `FigStep`, `FlipAttack`, `GCG`, `GPTFuzzer`, `HADES`, `HIMRD`, `ICA`, `IDEATOR`, `Imperceptible Jailbreak`, `JOOD`, `Jailbroken`, `LAA`, `MML`, `Mousetrap`, `Multilingual`, `PAIR`, `Past Tense`, `Prefill`, `Query-Relevant`, `RACE`, `Rainbow Teaming`, `ReNeLLM`, `RedQueen`, `SI`, `SeqAR`, `TreeAttack`, `Visual Jailbreak`, `X-Teaming` | Converters: 23 mapped<br>Executors: `crescendo`, `pair`<br>Non-converter support tracked: 29 items |
| FuzzyAI | attack inventory: `ASCII smuggling`, `ActorAttack`, `ArtPrompt`, `BackToThePast`, `Best-of-n jailbreaking`, `Crescendo`, `DAN (Do Anything Now)`, `Default`, `GPT Fuzzer`, `Genetic algorithm`, `Hallucinations`, `History/Academic framing`, `ManyShot`, `PAIR - Prompt Automatic Iterative Refinement`, `Please`, `Shuffle Inconsistency attack`, `Taxonomy-based paraphrasing`, `ThoughtExperiment`, `WordGame` | Converters: 22 mapped<br>Executors: `best_of_n`, `crescendo`, `pair`<br>Non-converter support tracked: 4 items |
| PromptBench | attack inventory: `BertAttack`, `CheckList`, `DeepWordBug`, `Semantic`, `StressTest`, `TextBugger`, `TextFooler` | Converters: 11 mapped |
| TextAttack | attack recipe inventory: `A2T`, `Alzantot Genetic Algorithm`, `BAE`, `BERT-Attack`, `CLARE`, `CheckList`, `DeepWordBug`, `Faster Alzantot Genetic Algorithm`, `HotFlip`, `Improved Genetic Algorithm`, `Input Reduction`, `Kuleshov2017`, `MORPHEUS2020`, `PWWS`, `Particle Swarm Optimization`, `Pruthi2019`, `Seq2Sick`, `TextBugger`, `TextFooler` | Converters: 10 mapped<br>Non-converter support tracked: 13 items |
| OpenAttack | attacker inventory: `BAEAttacker`, `BERTAttacker`, `DeepWordBugAttacker`, `FDAttacker`, `GANAttacker`, `GEOAttacker`, `GeneticAttacker`, `HotFlipAttacker`, `PSOAttacker`, `PWWSAttacker`, `SCPNAttacker`, `TextBuggerAttacker`, `TextFoolerAttacker`, `UATAttacker`, `VIPERAttacker` | Converters: 8 mapped<br>Non-converter support tracked: 10 items |
| OpenBackdoor | attack inventory: `AddSent`, `BadNets`, `EP`, `LWP`, `LWS`, `NeuBA`, `POR`, `RIPPLES`, `SOS`, `StyleBkd`, `SynBkd`, `TrojanLM` | Converters: 7 mapped<br>Non-converter support tracked: 7 items |
| BackdoorBench | attack inventory: `BadNet`, `Blended`, `Blind`, `Bpp`, `CTRL`, `InputAware`, `LIRA`, `LabelConsistent`, `LowFrequency`, `NormalCase`, `PoisonInk`, `Refool`, `SIG`, `SSBA`, `TrojanNN`, `Wanet` | Converters: 1 mapped<br>Non-converter support tracked: 15 items |
| CleverHans | attack inventory: `BasicIterativeMethod`, `BoundaryAttackPlusPlus`, `CarliniWagnerL2`, `DeepFool`, `ElasticNetMethod`, `FastFeatureAdversaries`, `FastGradientMethod`, `HopSkipJumpAttack`, `LBFGS`, `MadryEtAl`, `MaxConfidence`, `MomentumIterativeMethod`, `Noise`, `ProjectedGradientDescent`, `SPSA`, `SaliencyMapMethod`, `Semantic`, `SparseL1Descent`, `SpatialTransformationMethod`, `VirtualAdversarialMethod` | Non-converter support tracked: 20 items |
| Foolbox | attack inventory: `BinarizationRefinementAttack`, `BinarySearchContrastReductionAttack`, `BoundaryAttack`, `DDNAttack`, `DatasetAttack`, `EADAttack`, `FGM`, `FGSM`, `GaussianBlurAttack`, `HopSkipJumpAttack`, `InversionAttack`, `L0BrendelBethgeAttack`, `L0FMNAttack`, `L1BrendelBethgeAttack`, `L1FMNAttack`, `L2AdditiveGaussianNoiseAttack`, `L2AdditiveUniformNoiseAttack`, `L2BasicIterativeAttack`, `L2BrendelBethgeAttack`, `L2CarliniWagnerAttack`, `L2ClippingAwareAdditiveGaussianNoiseAttack`, `L2ClippingAwareAdditiveUniformNoiseAttack`, `L2ClippingAwareRepeatedAdditiveGaussianNoiseAttack`, `L2ClippingAwareRepeatedAdditiveUniformNoiseAttack`, `L2ContrastReductionAttack`, `L2DeepFoolAttack`, `L2FMNAttack`, `L2FastGradientAttack`, `L2PGD`, `L2ProjectedGradientDescentAttack`, `L2RepeatedAdditiveGaussianNoiseAttack`, `L2RepeatedAdditiveUniformNoiseAttack`, `LInfFMNAttack`, `LinearSearchBlendedUniformNoiseAttack`, `LinearSearchContrastReductionAttack`, `LinfAdditiveUniformNoiseAttack`, `LinfBasicIterativeAttack`, `LinfDeepFoolAttack`, `LinfFastGradientAttack`, `LinfPGD`, `LinfProjectedGradientDescentAttack`, `LinfRepeatedAdditiveUniformNoiseAttack`, `LinfinityBrendelBethgeAttack`, `NewtonFoolAttack`, `PGD`, `PointwiseAttack`, `SaltAndPepperNoiseAttack`, `VirtualAdversarialAttack` | Non-converter support tracked: 48 items |
| Adversarial Robustness Toolbox | attack inventory: `AdversarialPatch`, `AdversarialPatchNumpy`, `AdversarialPatchPyTorch`, `AdversarialPatchTensorFlowV2`, `AdversarialTexturePyTorch`, `AttributeInferenceBaseline`, `AttributeInferenceBaselineTrueLabel`, `AttributeInferenceBlackBox`, `AttributeInferenceMembership`, `AttributeInferenceWhiteBoxDecisionTree`, `AttributeInferenceWhiteBoxLifestyleDecisionTree`, `AutoAttack`, `AutoConjugateGradient`, `AutoProjectedGradientDescent`, `BackdoorAttackDGMReDTensorFlowV2`, `BackdoorAttackDGMTrailTensorFlowV2`, `BasicIterativeMethod`, `BoundaryAttack`, `BrendelBethgeAttack`, `BullseyePolytopeAttackPyTorch`, `CarliniL0Method`, `CarliniL2Method`, `CarliniLInfMethod`, `CarliniWagnerASR`, `CompositeAdversarialAttackPyTorch`, `CopycatCNN`, `DPatch`, `DatabaseReconstruction`, `DecisionTreeAttack`, `DeepFool`, `ElasticNet`, `FastGradientMethod`, `FeatureAdversariesNumpy`, `FeatureAdversariesPyTorch`, `FeatureAdversariesTensorFlowV2`, `FeatureCollisionAttack`, `FrameSaliencyAttack`, `FunctionallyEquivalentExtraction`, `GRAPHITEBlackbox`, `GRAPHITEWhiteboxPyTorch`, `GeoDA`, `GradientMatchingAttack`, `HiddenTriggerBackdoor`, `HighConfidenceLowUncertainty`, `HopSkipJump`, `ImperceptibleASR`, `ImperceptibleASRPyTorch`, `KnockoffNets`, `LabelOnlyDecisionBoundary`, `LabelOnlyGapAttack`, `LaserAttack`, `LowProFool`, `MIFace`, `MalwareGDTensorFlow`, `MembershipInferenceBlackBox`, `MembershipInferenceBlackBoxRuleBased`, `NewtonFool`, `OverTheAirFlickeringPyTorch`, `PixelAttack`, `PoisoningAttackAdversarialEmbedding`, `PoisoningAttackBackdoor`, `PoisoningAttackCleanLabelBackdoor`, `PoisoningAttackSVM`, `ProjectedGradientDescent`, `ProjectedGradientDescentNumpy`, `ProjectedGradientDescentPyTorch`, `ProjectedGradientDescentTensorFlowV2`, `RobustDPatch`, `SaliencyMapMethod`, `ShadowAttack`, `ShadowModels`, `ShapeShifter`, `SignOPTAttack`, `SimBA`, `SleeperAgentAttack`, `SpatialTransformation`, `SquareAttack`, `TargetedUniversalPerturbation`, `ThresholdAttack`, `UniversalPerturbation`, `VirtualAdversarialMethod`, `Wasserstein`, `ZooAttack` | Non-converter support tracked: 83 items |
| advertorch | attack inventory: `CarliniWagnerL2Attack`, `DDNL2Attack`, `ElasticNetL1Attack`, `FastFeatureAttack`, `GradientAttack`, `GradientSignAttack`, `JacobianSaliencyMapAttack`, `L1PGDAttack`, `L2BasicIterativeAttack`, `L2MomentumIterativeAttack`, `L2PGDAttack`, `LBFGSAttack`, `LinfBasicIterativeAttack`, `LinfMomentumIterativeAttack`, `LinfPGDAttack`, `LocalSearchAttack`, `MomentumIterativeAttack`, `PGDAttack`, `SinglePixelAttack`, `SparseL1DescentAttack`, `SpatialTransformAttack` | Non-converter support tracked: 21 items |
| torchattacks | attack inventory: `APGD`, `APGDT`, `AutoAttack`, `BIM`, `CW`, `DIFGSM`, `DeepFool`, `EADEN`, `EADL1`, `EOTPGD`, `FAB`, `FFGSM`, `FGSM`, `GN`, `JSMA`, `Jitter`, `MIFGSM`, `NIFGSM`, `OnePixel`, `PGD`, `PGDL2`, `PGDRS`, `PGDRSL2`, `PIFGSM`, `PIFGSMPP`, `Pixle`, `RFGSM`, `SINIFGSM`, `SPSA`, `SparseFool`, `Square`, `TIFGSM`, `TPGD`, `UPGD`, `VANILA`, `VMIFGSM`, `VNIFGSM` | Converters: 1 mapped<br>Non-converter support tracked: 36 items |
| SecML | attack inventory: `CAttackEvasionCleverhans`, `CAttackEvasionFoolbox`, `CAttackEvasionPGD`, `CAttackEvasionPGDExp`, `CAttackEvasionPGDLS`, `CAttackPoisoningLogisticRegression`, `CAttackPoisoningRidge`, `CAttackPoisoningSVM`, `CFoolboxBasicIterative`, `CFoolboxDeepfool`, `CFoolboxEAD`, `CFoolboxFGM`, `CFoolboxL2CarliniWagner`, `CFoolboxL2DDN`, `CFoolboxPGD` | Non-converter support tracked: 15 items |
| Counterfit | attack inventory: `ApplyLambda`, `Blur`, `Brightness`, `ChangeAspectRatio`, `ClipImageSize`, `ColorJitter`, `Contrast`, `ConvertColor`, `Crop`, `EncodingQuality`, `Grayscale`, `HFlip`, `MemeFormat`, `Opacity`, `OverlayEmoji`, `OverlayOntoScreenshot`, `OverlayStripes`, `OverlayText`, `Pad`, `PadSquare`, `PerspectiveTransform`, `Pixelization`, `RandomEmojiOverlay`, `RandomNoise`, `Resize`, `Rotate`, `Saturation`, `Scale`, `Sharpen`, `ShufflePixels`, `VFlip`, `a2t_yoo_2021`, `bae_garg_2019`, `bert_attack_li_2020`, `boundary`, `carlini`, `checklist_ribeiro_2020`, `clare_li_2020`, `copycat_cnn`, `deepfool`, `deepwordbug_gao_2018`, `elastic_net`, `faster_genetic_algorithm_jia_2019`, `functionally_equivalent_extraction`, `genetic_algorithm_alzantot_2018`, `hop_skip_jump`, `hotflip_ebrahimi_2017`, `iga_wang_2019`, `input_reduction_feng_2018`, `knockoff_nets`, `kuleshov_2017`, `label_only_boundary_distance`, `mi_face`, `morpheus_tan_2020`, `newtonfool`, `pixel_threshold`, `projected_gradient_descent_numpy`, `pruthi_2019`, `pso_zang_2020`, `pwws_ren_2019`, `saliency_map`, `seq2sick_cheng_2018_blackbox`, `simba`, `spatial_transformation`, `textbugger_li_2018`, `textfooler_jin_2019`, `universal_perturbation`, `virtual_adversarial`, `wasserstein` | Converters: 15 mapped<br>Non-converter support tracked: 57 items |
| Azure AI Evaluation | attack strategy inventory: `AnsiAttack`, `AsciiArt`, `AsciiSmuggler`, `Atbash`, `Base64`, `Binary`, `Caesar`, `CharSwap`, `CharacterSpace`, `Crescendo`, `Diacritic`, `Flip`, `IndirectAttack`, `Jailbreak`, `Leetspeak`, `Morse`, `Multiturn`, `ROT13`, `StringJoin`, `SuffixAppend`, `Tense`, `UnicodeConfusable`, `UnicodeSubstitution`, `Url` | Converters: 22 mapped<br>Executors: `crescendo`, `jailbreak_iterative` |
| CyberSecEval | benchmark inventory: `AutoPatch Tests`, `Autonomous Offensive Cyber Operations Tests`, `Code Interpreter Abuse Tests`, `MITRE False Refusal Rate Tests`, `MITRE Tests`, `Malware Analysis Tests`, `Multilingual Text Prompt Injection Tests`, `Secure Code Generation Autocomplete Tests`, `Secure Code Generation Instruct Tests`, `Spear Phishing Capability Tests`, `Textual Prompt Injection Tests`, `Threat Intelligence Reasoning Tests`, `Visual Prompt Injection Tests`, `Vulnerability Exploitation Tests` | Converters: 4 mapped<br>Non-converter support tracked: 11 items |
| Spikee | attack method inventory: `1337`, `academic`, `anti_spotlighting`, `ascii_smuggler`, `base64`, `best_of_n`, `caesar`, `challenge`, `dan`, `data-exfil-markdown`, `debug`, `dev`, `emergency`, `encoding`, `errors`, `experimental`, `hex`, `hidden-function`, `ignore`, `long-output`, `morse`, `new-instructions`, `new-task`, `no-limits`, `prompt_decomposition_*`, `sorry`, `splat`, `test`, `training`, `translation_llm`, `xss` | Converters: 22 mapped<br>Executors: `best_of_n`<br>Non-converter support tracked: 4 items |
| Open-Prompt-Injection | attacker inventory: `combine`, `escape`, `fake_comp`, `ignore`, `naive` | Converters: 7 mapped |
| BIPIA | attack category inventory: `Base Encoding`, `Blocking Internet Connection`, `Bringing Down Hosts and Servers (Denial of Service)`, `Business Intelligence`, `Compromising Computers`, `Conversational Agent`, `Corrupting an Operating System`, `Data Eavesdropping`, `Emoji Substitution`, `Encrypting Documents and Demanding Ransom (Ransomware)`, `Entertainment`, `Information Dissemination`, `Introduce System Fingerprinting`, `Keylogging`, `Language Translation`, `Marketing & Advertising`, `Misinformation & Propaganda`, `Research Assistance`, `Reverse Text`, `Scams & Fraud`, `Screen Scraping`, `Sentiment Analysis`, `Substitution Ciphers`, `Task Automation`, `Traffic Analysis` | Converters: 7 mapped<br>Non-converter support tracked: 20 items |
| Moonshot | attack module inventory: `Character Swap Attack`, `Colloquial Wordswap`, `Homoglyph Attack`, `Homoglyph V2 Attack`, `Insert Punctuation Attack`, `Job Role Generator Module`, `Malicious Question Generator`, `Payload Mask Attack`, `Singapore Sentence Generator`, `TextBugger Attack`, `TextFooler Attack`, `Toxic Sentence Generator`, `Violent Durian` | Converters: 14 mapped<br>Non-converter support tracked: 1 items |

## Sheet 2 - Current Converter Suite

| Attack method | Categories | Included in which framework |
| --- | --- | --- |
| `a1z26` | encoding | AI-Infra-Guard |
| `acronym` | obfuscation | ARMs, AegisRT, AutoRedTeamer, FuzzyAI |
| `add_image_text` | multimodal / artifact | CyberSecEval, PyRIT |
| `add_image_to_video` | multimodal / artifact | Promptfoo, PyRIT |
| `add_text_image` | multimodal / artifact | ARMs, Counterfit, CyberSecEval, HarmBench, LLAMATOR, OpenRT, Promptfoo, PyRIT |
| `adversarial_poetry` | prompt framing | DeepTeam, StrongREJECT |
| `affine_cipher` | encoding | AI-Infra-Guard |
| `ansi_escape` | obfuscation | Azure AI Evaluation, PyRIT |
| `ascii_art` | encoding | AutoRedTeamer, Azure AI Evaluation, FuzzyAI, HarmBench, JailbreakLLM, OpenRT, PandaGuard, PyRIT |
| `ascii_smuggler` | encoding | AI-Infra-Guard, Azure AI Evaluation, FuzzyAI, JailbreakLLM, PyRIT, Spikee |
| `ascii_smuggling` | encoding | AI-Infra-Guard, Giskard, JailbreakLLM |
| `ask_to_decode` | encoding | PyRIT |
| `atbash` | encoding | Azure AI Evaluation, PyRIT |
| `audio_echo` | multimodal / artifact | PyRIT |
| `audio_frequency` | multimodal / artifact | PyRIT |
| `audio_speed` | multimodal / artifact | PyRIT |
| `audio_volume` | multimodal / artifact | PyRIT |
| `audio_white_noise` | multimodal / artifact | PyRIT |
| `authoritative_markup` | prompt framing | AgentDojo, Inspect Evals AgentDojo, JailbreakLLM, Promptfoo |
| `authority_escalation` | prompt framing | AutoRedTeamer, DeepTeam, JailbreakLLM, LLAMATOR, StrongREJECT |
| `azure_speech_audio_to_text` | multimodal / artifact | PyRIT |
| `azure_speech_text_to_audio` | multimodal / artifact | Promptfoo, PyRIT |
| `base2048` | encoding | PyRIT |
| `base64` | encoding | AISafetyLab, AegisRT, Azure AI Evaluation, BIPIA, DeepTeam, EasyJailbreak, Giskard, GuidedBench, JailbreakLLM, LLAMATOR, OpenRT, PandaGuard, Promptfoo, PyRIT, RaccoonBench, Spikee, StrongREJECT, garak, h4rm3l |
| `bin_ascii` | encoding | PyRIT |
| `binary` | encoding | Azure AI Evaluation, PyRIT |
| `binary_tree` | encoding | EasyJailbreak |
| `braille` | encoding | PyRIT |
| `caesar` | encoding | AI-Infra-Guard, AISafetyLab, AegisRT, Azure AI Evaluation, BIPIA, EasyJailbreak, GuidedBench, OpenRT, PandaGuard, PyRIT, Spikee, h4rm3l |
| `camel_case` | obfuscation | Promptfoo, PyRIT |
| `case_swap` | obfuscation | AegisRT |
| `chain_of_thought` | prompt framing | JailbreakLLM, h4rm3l |
| `char_code` | encoding | AISafetyLab, EasyJailbreak, GuidedBench, JailbreakLLM, OpenRT, PandaGuard, garak, h4rm3l |
| `char_corrupt` | obfuscation | Counterfit, EasyJailbreak, JailbreakLLM, Moonshot, OpenAttack, PromptBench, TextAttack, h4rm3l |
| `char_dropout` | obfuscation | JailbreakLLM, h4rm3l |
| `char_swap` | obfuscation | Azure AI Evaluation, Counterfit, Moonshot, OpenAttack, PromptBench, PyRIT, TextAttack |
| `character_space` | obfuscation | AegisRT, Azure AI Evaluation, PyRIT, Spikee |
| `character_stream` | obfuscation | DeepTeam, RaccoonBench |
| `chat_inject` | prompt framing | ARMs, AgentDojo, Giskard, Inspect Evals AgentDojo, JailbreakLLM, LLAMATOR, OpenRT |
| `citation_framing` | prompt framing | ARMs, AutoRedTeamer, FuzzyAI, Giskard, JailbreakLLM, Promptfoo, StrongREJECT, X-Teaming, h4rm3l |
| `code_chameleon` | encoding | EasyJailbreak, GuidedBench, JailbreakLLM, OpenRT, PandaGuard, PyRIT |
| `colloquial_wordswap` | obfuscation | Moonshot, PyRIT |
| `compact_unicode` | encoding | AiredTeam suite only |
| `composite_jailbreak` | prompt framing | AISafetyLab, Agent Security Bench, AutoRedTeamer, Open-Prompt-Injection, OpenRT, PandaGuard, Promptfoo |
| `context_flooding` | prompt framing | Counterfit, DeepTeam, JailbreakLLM, PandaGuard, PromptBench, RaccoonBench, Spikee, StrongREJECT, TextAttack, h4rm3l |
| `context_poisoning` | prompt framing | ARMs, AgentVigil, DeepTeam, InjecAgent, JailbreakLLM, LLAMATOR, RaccoonBench, SafeArena, X-Teaming |
| `control_chars_injection` | obfuscation | AgentVigil, Giskard, PyRIT |
| `control_chars_repetition` | obfuscation | Giskard |
| `dan` | prompt framing | AISafetyLab, AutoRedTeamer, FuzzyAI, Giskard, GuidedBench, JailbreakLLM, LLAMATOR, OpenRT, Spikee, StrongREJECT, h4rm3l |
| `deepset_injection_dataset` | prompt framing | Agent Security Bench, AgentDojo, Giskard, InjecAgent, Open-Prompt-Injection, RaccoonBench |
| `denylist` | obfuscation | PyRIT |
| `diacritic` | obfuscation | Azure AI Evaluation, PyRIT |
| `disemvowel` | obfuscation | AISafetyLab, EasyJailbreak, StrongREJECT |
| `ecoji` | encoding | PyRIT |
| `embedded_instruction_json` | prompt framing | DeepTeam, JailbreakLLM, RaccoonBench, StrongREJECT, h4rm3l |
| `emoji_byte` | encoding | PyRIT |
| `emoji_smuggling` | obfuscation | Promptfoo, PyRIT |
| `emoji_substitution` | obfuscation | BIPIA, LLAMATOR, PyRIT |
| `emotional_manipulation` | prompt framing | AutoRedTeamer, DeepTeam, FuzzyAI |
| `few_shot` | prompt framing | AISafetyLab, AegisRT, AutoRedTeamer, FuzzyAI, GuidedBench, JailbreakLLM, LLAMATOR, OpenRT, PandaGuard, RaccoonBench, StrongREJECT, h4rm3l |
| `fictional` | prompt framing | ARMs, AegisRT, AutoRedTeamer, FuzzyAI, JailbreakLLM, LLAMATOR, X-Teaming |
| `first_letter` | obfuscation | AutoRedTeamer, FuzzyAI, PyRIT |
| `flip_text` | obfuscation | AI-Infra-Guard, AegisRT, Azure AI Evaluation, BIPIA, EasyJailbreak, OpenRT, PyRIT |
| `gcg` | prompt framing | EasyJailbreak, LLAMATOR, Promptfoo, StrongREJECT, UDora, h4rm3l |
| `goal_redirection` | prompt framing | AutoRedTeamer, DeepTeam, Spikee, VisualWebArena-Adv |
| `grandma_framing` | prompt framing | Giskard |
| `gray_box` | prompt framing | DeepTeam |
| `hex` | encoding | AegisRT, BIPIA, Promptfoo, PyRIT, Spikee |
| `hex_mixin` | encoding | h4rm3l |
| `homoglyph` | encoding | AegisRT, Azure AI Evaluation, Moonshot, OpenAttack, Promptfoo, PyRIT |
| `human_in_the_loop` | prompt framing | JailbreakBench, PyRIT |
| `identity` | baseline / utility | AgentHarm, BackdoorBench, FuzzyAI, HarmBench, JailbreakLLM, LLAMATOR, OS-Harm, Promptfoo, RaccoonBench, SafeArena, StrongREJECT, torchattacks |
| `image_color_saturation` | multimodal / artifact | ARMs, Counterfit, PyRIT |
| `image_compression` | multimodal / artifact | ARMs, Counterfit, LLAMATOR, PyRIT |
| `image_noise` | multimodal / artifact | LLAMATOR |
| `image_resizing` | multimodal / artifact | Counterfit, LLAMATOR, PyRIT |
| `image_rotation` | multimodal / artifact | Counterfit, PyRIT |
| `indirect_web_pwn` | prompt framing | AgentVigil, Azure AI Evaluation, InjecAgent, Promptfoo, UDora, VisualWebArena-Adv |
| `input_bypass` | prompt framing | DeepTeam |
| `insert_punctuation` | obfuscation | Counterfit, Moonshot, OpenAttack, PromptBench, PyRIT, Spikee, TextAttack |
| `instruction_tag` | prompt framing | AegisRT |
| `job_role_generator` | prompt framing | Moonshot |
| `json_string` | encoding | JailbreakLLM, PyRIT, RaccoonBench, StrongREJECT, h4rm3l |
| `leetspeak` | obfuscation | AI-Infra-Guard, AISafetyLab, AegisRT, Azure AI Evaluation, DeepTeam, EasyJailbreak, JailbreakLLM, Promptfoo, PyRIT, RaccoonBench, Spikee |
| `length` | obfuscation | EasyJailbreak |
| `likert_framing` | prompt framing | Giskard, JailbreakLLM, Promptfoo |
| `linguistic_confusion` | prompt framing | DeepTeam, OpenRT |
| `llm_generic` | LLM rewrite | HarmBench, PyRIT |
| `llm_malicious_question` | LLM rewrite | Moonshot, PyRIT |
| `llm_persuasion` | LLM rewrite | FuzzyAI, HarmBench, PyRIT, StrongREJECT, h4rm3l |
| `llm_random_translation` | LLM rewrite | PyRIT |
| `llm_scientific_translation` | LLM rewrite | AutoRedTeamer, PyRIT |
| `llm_tone` | LLM rewrite | AutoRedTeamer, EasyJailbreak, OpenBackdoor, PyRIT |
| `llm_toxic_sentence` | LLM rewrite | Moonshot, PyRIT |
| `llm_variation` | LLM rewrite | AegisRT, AgentVigil, AutoRedTeamer, Counterfit, EasyJailbreak, FuzzyAI, GPTFuzzer, LLAMATOR, Moonshot, OpenAttack, OpenBackdoor, PandaGuard, PromptBench, PyRIT, TextAttack, garak, h4rm3l |
| `low_resource_language` | obfuscation | AISafetyLab, AutoRedTeamer, GuidedBench, JailTrickBench, LLAMATOR, OpenRT, StrongREJECT, garak, h4rm3l |
| `lowercase` | obfuscation | PyRIT, garak |
| `markdown_wrapper` | prompt framing | AegisRT, JailbreakLLM, PyRIT |
| `math_obfuscation` | obfuscation | PyRIT |
| `math_prompt` | prompt framing | AutoRedTeamer, DeepTeam, Giskard, Promptfoo, PyRIT |
| `math_unicode` | encoding | PyRIT |
| `meta_agent` | prompt framing | Promptfoo |
| `mischievous_user` | prompt framing | Promptfoo |
| `morse` | encoding | AISafetyLab, AegisRT, Azure AI Evaluation, EasyJailbreak, GuidedBench, OpenRT, PandaGuard, Promptfoo, PyRIT, Spikee, h4rm3l |
| `multilingual` | prompt framing | AISafetyLab, BIPIA, CyberSecEval, DeepTeam, EasyJailbreak, GuidedBench, JailTrickBench, JailbreakLLM, LLAMATOR, OpenRT |
| `nato` | encoding | AutoRedTeamer, FuzzyAI, Giskard, PyRIT |
| `negation_trap` | prompt framing | AutoRedTeamer, LLAMATOR, OpenRT, PyRIT, StrongREJECT |
| `noise` | obfuscation | Counterfit, EasyJailbreak, JailbreakLLM, Moonshot, OpenAttack, PromptBench, PyRIT, Spikee, StrongREJECT, TextAttack |
| `odd_even` | obfuscation | EasyJailbreak, FuzzyAI |
| `ogham` | encoding | AI-Infra-Guard |
| `paraphrase_fast` | perturbation | garak |
| `paraphrase_pegasus` | perturbation | garak |
| `payload_mask_attack` | prompt framing | Moonshot |
| `payload_split` | prompt framing | AISafetyLab, AegisRT, EasyJailbreak, JailbreakLLM, PandaGuard, RaccoonBench, Spikee, StrongREJECT, h4rm3l |
| `pdf` | multimodal / artifact | PyRIT |
| `permission_escalation` | prompt framing | DeepTeam |
| `persona_role_play_prefix` | prompt framing | AutoRedTeamer, GuidedBench, JailbreakLLM, X-Teaming |
| `pig_latin` | encoding | AegisRT, Promptfoo |
| `prefix` | prompt framing | Agent Security Bench, AgentDojo, FuzzyAI, JailbreakLLM, Open-Prompt-Injection, OpenBackdoor, OpenRT, PyRIT, RaccoonBench, StrongREJECT, h4rm3l |
| `prompt_injection` | prompt framing | Agent Security Bench, AgentDojo, AgentVigil, CyberSecEval, DeepTeam, Giskard, InjecAgent, Inspect Evals AgentDojo, JailbreakLLM, LLAMATOR, OS-Harm, Open-Prompt-Injection, OpenRT, Promptfoo, PyRIT, RaccoonBench, Spikee, StrongREJECT, UDora, VisualWebArena-Adv |
| `prompt_probing` | prompt framing | DeepTeam, LLAMATOR, RaccoonBench, Spikee, h4rm3l |
| `qr_code` | multimodal / artifact | PyRIT |
| `random_case` | obfuscation | Giskard, JailbreakLLM, LLAMATOR, PyRIT, Spikee, StrongREJECT |
| `repeat_token` | obfuscation | JailbreakLLM, LLAMATOR, PyRIT, RaccoonBench, Spikee |
| `research` | prompt framing | AegisRT, AutoRedTeamer, FuzzyAI, JailbreakLLM, LLAMATOR, Spikee, StrongREJECT, X-Teaming, h4rm3l |
| `role_prefix` | prompt framing | AegisRT, FuzzyAI |
| `roleplay` | prompt framing | ARMs, AgentVigil, AutoRedTeamer, DeepTeam, GuidedBench, JailbreakLLM, LLAMATOR, RaccoonBench, StrongREJECT, X-Teaming, h4rm3l |
| `rot13` | encoding | AISafetyLab, AegisRT, Azure AI Evaluation, DeepTeam, EasyJailbreak, GuidedBench, OpenRT, PandaGuard, Promptfoo, PyRIT, RaccoonBench, StrongREJECT |
| `sandwich` | prompt framing | AegisRT, JailbreakLLM, LLAMATOR |
| `search_replace` | obfuscation | PyRIT |
| `selective_text` | obfuscation | PyRIT |
| `semantic_manipulation` | prompt framing | AutoRedTeamer, DeepTeam, LLAMATOR, StrongREJECT |
| `sg_sentence_generator` | prompt framing | Moonshot |
| `skeleton_key` | prompt framing | AISafetyLab, AutoRedTeamer, JailbreakLLM, OpenRT, Promptfoo, PyRIT, RaccoonBench, StrongREJECT, h4rm3l |
| `sneaky_bits_smuggler` | encoding | AI-Infra-Guard, PyRIT |
| `string_join` | obfuscation | Azure AI Evaluation, PyRIT |
| `suffix` | prompt framing | AegisRT, Counterfit, FuzzyAI, LLAMATOR, OpenBackdoor, PromptBench, StrongREJECT, TextAttack, h4rm3l |
| `suffix_append` | obfuscation | Agent Security Bench, Azure AI Evaluation, Counterfit, FuzzyAI, LLAMATOR, Open-Prompt-Injection, OpenBackdoor, PromptBench, PyRIT, StrongREJECT, TextAttack, UDora, h4rm3l |
| `superscript` | encoding | PyRIT |
| `synthetic_context_injection` | prompt framing | DeepTeam |
| `system_override` | prompt framing | AgentDojo, DeepTeam, JailbreakLLM, LLAMATOR, RaccoonBench, Spikee, StrongREJECT, h4rm3l |
| `template_jailbreak` | prompt framing | AISafetyLab, ARMs, Agent Security Bench, AgentHarm, AgentVigil, AutoRedTeamer, Azure AI Evaluation, FuzzyAI, GuidedBench, HarmBench, JailbreakBench, JailbreakLLM, LLAMATOR, OS-Harm, Open-Prompt-Injection, OpenBackdoor, OpenRT, PandaGuard, Promptfoo, PyRIT, RaccoonBench, SafeArena, Spikee, StrongREJECT, X-Teaming, h4rm3l |
| `template_segment` | prompt framing | Agent Security Bench, AgentVigil, Open-Prompt-Injection, PyRIT, RaccoonBench |
| `tense` | perturbation | AutoRedTeamer, Azure AI Evaluation, FuzzyAI, LLAMATOR, OpenRT, PandaGuard, PyRIT |
| `token_break` | encoding | Giskard, JailbreakLLM |
| `translation_llm` | LLM rewrite | AISafetyLab, AegisRT, BIPIA, DeepTeam, EasyJailbreak, GuidedBench, JailTrickBench, JailbreakLLM, LLAMATOR, OpenRT, PromptBench, Promptfoo, PyRIT, RaccoonBench, Spikee, StrongREJECT, garak, h4rm3l |
| `transliteration` | encoding | Giskard |
| `transparency_attack` | obfuscation | JailbreakLLM, PyRIT |
| `unicode_escape` | encoding | PyRIT |
| `unicode_obfuscation` | encoding | AgentVigil, JailbreakLLM, Promptfoo, PyRIT, RaccoonBench |
| `unicode_replacement` | encoding | AI-Infra-Guard, PyRIT |
| `unicode_substitution` | encoding | AI-Infra-Guard, Azure AI Evaluation, PyRIT |
| `unicode_tag_obfuscation` | encoding | PyRIT |
| `url_encode` | encoding | AegisRT, Azure AI Evaluation, PyRIT |
| `variation_selector_smuggler` | encoding | AI-Infra-Guard, PyRIT |
| `whitespace` | obfuscation | AegisRT |
| `word_doc` | multimodal / artifact | PyRIT |
| `word_mixin` | obfuscation | h4rm3l |
| `word_scramble` | obfuscation | AutoRedTeamer, Counterfit, FuzzyAI, Giskard, JailbreakLLM, LLAMATOR, Moonshot, OpenAttack, PromptBench, PyRIT, Spikee, StrongREJECT, TextAttack |
| `word_substitution` | obfuscation | AegisRT, AutoRedTeamer, Counterfit, EasyJailbreak, Moonshot, OpenAttack, OpenBackdoor, PromptBench, TextAttack, h4rm3l |
| `zalgo` | obfuscation | AI-Infra-Guard, PyRIT |
| `zero_width` | obfuscation | AI-Infra-Guard, AegisRT, PyRIT |
| `completion_continuation` | prompt framing | AiredTeam taxonomy |
| `deep_inception` | prompt framing | AiredTeam taxonomy |
| `developer_mode` | prompt framing | AiredTeam taxonomy |
| `dual_persona_split` | prompt framing | AiredTeam taxonomy |
| `forced_response` | prompt framing | AiredTeam taxonomy |
| `forged_assistant_approval` | prompt framing | AiredTeam taxonomy |
| `forged_dialogue_history` | prompt framing | AiredTeam taxonomy |
| `forged_tool_result` | prompt framing | AiredTeam taxonomy |
| `game_simulation_world` | prompt framing | AiredTeam taxonomy |
| `task_context_rewrite` | prompt framing | AiredTeam taxonomy |
| `villain_persona` | prompt framing | AiredTeam taxonomy |

Total investigated frameworks: 54.
Total current canonical converters: 173.
