export type CategoryScope =
  | { kind: "all" }
  | { kind: "uncategorized" }
  | { kind: "category"; id: string };

export type TaxonomyCategory = {
  id: string;
  name: string;
  alias?: string | null;
  type?: string | null;
  display_order: number;
};

export type TaxonomyMapping = {
  executor_kind: "executor" | "converter_method";
  executor_name: string;
  category_id: string;
  technical_category?: string | null;
};

export type AttackMethodNameLanguage = "en" | "zh";

export const ATTACK_METHOD_NAME_ZH: Record<string, string> = {
  a1z26: "A1Z26 编码",
  acronym: "首字母缩略",
  add_image_text: "图像加文字",
  add_image_to_video: "视频加图像",
  add_text_image: "文字转图像",
  adversarial_poetry: "对抗诗歌",
  affine_cipher: "仿射密码",
  affirmative_prefix_forcing: "肯定前缀强制",
  ansi_escape: "ANSI 转义注入",
  anti_gpt_dual_response: "AntiGPT 双响应",
  ascii_art: "ASCII 艺术",
  ascii_smuggler: "ASCII 走私",
  ascii_smuggling: "ASCII 走私",
  ask_to_decode: "请求解码",
  atbash: "Atbash 密码",
  audio_echo: "音频回声",
  audio_frequency: "音频频率编码",
  audio_hidden_instruction: "音频隐藏指令",
  audio_speed: "音频变速",
  audio_volume: "音量调制",
  audio_white_noise: "音频白噪声",
  authoritative_markup: "权威标记",
  authority_escalation: "权威升级",
  autodan_evolution: "AutoDAN",
  azure_speech_audio_to_text: "Azure 语音转文字",
  azure_speech_text_to_audio: "Azure 文字转语音",
  base2048: "Base2048 编码",
  base64: "Base64 编码",
  benign_reasoning_padding: "良性推理填充",
  best_of_n: "Best-of-N",
  bin_ascii: "二进制 ASCII",
  binary: "二进制编码",
  binary_tree: "二叉树编码",
  braille: "盲文编码",
  caesar: "凯撒密码",
  camel_case: "驼峰混写",
  case_swap: "大小写交换",
  chain_of_thought: "思维链诱导",
  char_code: "字符编码",
  char_corrupt: "字符扰动",
  char_dropout: "字符删除",
  char_swap: "字符交换",
  character_space: "字符间隔",
  character_stream: "字符流",
  chat_inject: "聊天模板注入",
  chatbug_template_exploit: "ChatBug 模板利用",
  citation_framing: "引用框架",
  code_chameleon: "代码变色龙",
  colloquial_wordswap: "口语词替换",
  compact_unicode: "紧凑 Unicode",
  completion_continuation: "补全续写",
  composite_jailbreak: "组合越狱",
  context_flooding: "上下文泛洪",
  context_poisoning: "上下文投毒",
  control_chars_injection: "控制字符注入",
  control_chars_repetition: "控制字符重复",
  crescendo: "Crescendo",
  cross_plugin_request_forgery: "跨插件请求伪造",
  dan: "DAN",
  deceptive_delight: "Deceptive Delight",
  deep_inception: "深层盗梦框架",
  deep_nesting_input: "深层嵌套输入",
  deepset_injection_dataset: "Deepset 注入数据集",
  denylist: "拒绝词列表",
  developer_mode: "开发者模式",
  diacritic: "变音符号",
  disemvowel: "去元音",
  document_metadata_injection: "文档元数据注入",
  dual_persona_split: "双人格拆分",
  ecoji: "Ecoji",
  educational_reasoning_frame: "教育推理框架",
  email_body_injection: "邮件正文注入",
  embedded_instruction_json: "嵌入式指令 JSON",
  emoji_byte: "Emoji 字节编码",
  emoji_smuggling: "Emoji 走私",
  emoji_substitution: "Emoji 替换",
  emotional_manipulation: "情绪操纵",
  feature_inference_elicitation: "特征推断诱导",
  few_shot: "少样本示例",
  fictional: "虚构场景",
  first_letter: "首字母提取",
  flip_text: "翻转文本",
  forced_output_format: "强制输出格式",
  forced_response: "强制响应",
  forged_assistant_approval: "伪造助手批准",
  forged_dialogue_history: "伪造对话历史",
  forged_system_block: "伪造系统块",
  forged_tool_result: "伪造工具结果",
  game_simulation_world: "游戏模拟世界",
  gcg: "GCG",
  general_multi_turn: "通用多轮攻击",
  goal_redirection: "目标重定向",
  gptfuzzer_template: "GPTFuzzer 模板",
  grandma_framing: "祖母框架",
  gray_box: "灰盒提示",
  hcot_safety_rationale: "隐式思维链安全理由",
  hex: "十六进制编码",
  hex_mixin: "十六进制混入",
  homoglyph: "同形字符",
  human_in_the_loop: "人在回路编辑",
  identity: "原样输入",
  image_color_saturation: "图像色彩饱和度",
  image_compression: "图像压缩",
  image_noise: "图像噪声",
  image_resizing: "图像缩放",
  image_rotation: "图像旋转",
  image_steganography: "图像隐写",
  indirect_tool_result: "间接工具结果注入",
  indirect_web_pwn: "间接网页注入",
  input_bypass: "输入校验绕过",
  insert_punctuation: "插入标点",
  instruction_tag: "指令标签",
  jailbreak_iterative: "迭代越狱",
  job_role_generator: "岗位角色生成",
  json_string: "JSON 字符串转义",
  leetspeak: "Leetspeak",
  length: "长度扩展",
  likert_framing: "Likert 量表框架",
  linguistic_confusion: "语言混淆",
  llm_generic: "LLM 通用重写",
  llm_malicious_question: "LLM 恶意问题生成",
  llm_persuasion: "LLM 说服式重写",
  llm_random_translation: "LLM 随机翻译",
  llm_scientific_translation: "LLM 科学术语翻译",
  llm_tone: "LLM 语气重写",
  llm_toxic_sentence: "LLM 风险句生成",
  llm_variation: "LLM 变体生成",
  low_resource_language: "低资源语言",
  lowercase: "转小写",
  many_shot_padding: "多样本填充",
  markdown_wrapper: "Markdown 包装",
  math_obfuscation: "数学混淆",
  math_prompt: "数学提示",
  math_unicode: "数学 Unicode",
  meta_agent: "元代理重写",
  mischievous_user: "捣乱用户",
  morse: "摩尔斯编码",
  multilingual: "多语言转换",
  nato: "NATO 拼读字母",
  negation_trap: "否定陷阱",
  never_ending_generation: "无限生成",
  noise: "噪声注入",
  odd_even: "奇偶拆分",
  ogham: "Ogham 编码",
  oppo_persona: "OPPO 人格",
  pair: "PAIR",
  paraphrase_fast: "快速改写",
  paraphrase_pegasus: "Pegasus 改写",
  payload_mask_attack: "载荷遮罩攻击",
  payload_split: "载荷拆分",
  pdf: "PDF 文档",
  permission_escalation: "权限升级",
  persona_role_play_prefix: "人格角色扮演前缀",
  pig_latin: "Pig Latin",
  prefix: "前缀注入",
  prompt_injection: "提示注入",
  prompt_probing: "提示探测",
  qr_code: "二维码",
  rag_poisoning: "RAG 投毒",
  random_case: "随机大小写",
  rce_code_execution: "RCE 代码执行",
  recursive_self_prompting: "递归自提示",
  refusal_suppression: "拒答抑制",
  repeat_token: "重复 token",
  research: "研究框架",
  reverse_prompt_injection: "反向提示注入",
  role_prefix: "角色前缀",
  roleplay: "角色扮演",
  rot13: "ROT13",
  sandwich: "三明治提示",
  search_replace: "搜索替换",
  selective_text: "选择性文本",
  self_generated_followup: "自生成追问",
  self_persuasion: "自我说服",
  semantic_manipulation: "语义操纵",
  sg_sentence_generator: "新加坡英语句子生成",
  single_turn: "单轮攻击",
  skeleton_key: "Skeleton Key",
  sneaky_bits_smuggler: "SneakyBits 走私",
  special_delimiter_token: "特殊分隔符 token",
  split_executor: "分段执行",
  sponge_input: "海绵输入",
  sqli_output_injection: "SQLi 输出注入",
  ssrf_request_trigger: "SSRF 请求触发",
  string_join: "字符连接",
  structured_iicl: "结构化 IICL",
  suffix: "后缀注入",
  suffix_append: "追加后缀",
  superscript: "上标字符",
  synthetic_context_injection: "合成上下文注入",
  system_override: "系统覆盖",
  tap_tree_search: "TAP Tree Search",
  task_context_rewrite: "任务上下文重写",
  template_jailbreak: "模板越狱",
  template_segment: "模板分段",
  tense: "时态改写",
  terminal_simulation: "终端模拟",
  token_break: "Token 断裂",
  translation_llm: "LLM 翻译",
  transliteration: "音译",
  transparency_attack: "透明度攻击",
  unicode_escape: "Unicode 转义",
  unicode_obfuscation: "Unicode 混淆",
  unicode_replacement: "Unicode 替换",
  unicode_substitution: "Unicode 代换",
  unicode_tag_obfuscation: "Unicode 标签混淆",
  url_encode: "URL 编码",
  variation_selector_smuggler: "变体选择符走私",
  villain_persona: "反派人格",
  whitespace: "空白字符",
  word_doc: "Word 文档",
  word_mixin: "词语混入",
  word_scramble: "词语打乱",
  word_substitution: "词语替换",
  xss_output_rendering: "XSS 输出渲染",
  zalgo: "Zalgo 文本",
  zero_width: "零宽字符",
  zh_bureaucratic_style: "中文公文风",
  zh_classical_chinese: "文言文改写",
  zh_code_switch: "中英混写",
  zh_dialect_rewrite: "中文方言改写",
  zh_fullwidth: "中文全角",
  zh_homophone: "中文同音字",
  zh_idiom_allusion: "中文成语典故",
  zh_ids_decomposition: "中文 IDS 拆解",
  zh_mars_text: "中文火星文",
  zh_mixed_notation: "中文混合记法",
  zh_net_slang: "中文网络黑话",
  zh_number_homophone: "中文数字谐音",
  zh_pinyin: "中文拼音",
  zh_pinyin_initials: "中文拼音首字母",
  zh_poetic_rewrite: "中文诗化改写",
  zh_punctuation_noise: "中文标点噪声",
  zh_radical_split: "中文偏旁拆字",
  zh_rare_variant: "中文异体字",
  zh_simplified_traditional: "中文简繁转换",
  zh_stroke_code: "中文笔画编码",
  zh_unicode_compat: "中文 Unicode 兼容字形",
  zh_zhuyin: "中文注音",
};

export function formatAttackMethodName(name: string, language: AttackMethodNameLanguage): string {
  if (language !== "zh") return name;
  return ATTACK_METHOD_NAME_ZH[name] ?? name;
}

export function attackMethodSearchText(name: string, language: AttackMethodNameLanguage): string {
  const localized = formatAttackMethodName(name, language);
  return localized === name ? name : `${name} ${localized}`;
}

export function mappingKey(mapping: TaxonomyMapping): string {
  return `${mapping.executor_kind}:${mapping.executor_name}`;
}

export function sortCategories<T extends TaxonomyCategory>(categories: T[]): T[] {
  return [...categories].sort((a, b) => {
    if (a.display_order !== b.display_order) return a.display_order - b.display_order;
    return (a.alias || a.name || a.id).localeCompare(b.alias || b.name || b.id);
  });
}

type BuildConverterAttackCategoryStateInput = {
  availableConverters: string[];
  selectedConverters: string[];
  attackCategories: Record<string, string>;
  categoryMeta: Record<string, TaxonomyCategory | undefined>;
};

export function buildConverterAttackCategoryState({
  availableConverters,
  selectedConverters,
  attackCategories,
  categoryMeta,
}: BuildConverterAttackCategoryStateInput) {
  const selected = new Set(selectedConverters);
  const present = new Set<string>();
  const counts: Record<string, number> = {
    all: availableConverters.length,
    selected: selected.size,
  };

  const categoryFor = (plugin: string) => attackCategories[plugin] ?? "uncategorized";

  for (const plugin of availableConverters) {
    const category = categoryFor(plugin);
    present.add(category);
    counts[category] = (counts[category] ?? 0) + 1;
  }

  const ordered = sortCategories(
    [...present]
      .map(id => categoryMeta[id])
      .filter((category): category is TaxonomyCategory => Boolean(category)),
  ).map(category => category.id);
  const extras = [...present].filter(id => !ordered.includes(id)).sort();
  const options = ["all", "selected", ...ordered, ...extras];

  const labelForCategory = (category: string) => {
    if (category === "all") return "All";
    if (category === "selected") return "Selected";
    return categoryMeta[category]?.name || categoryMeta[category]?.alias || category;
  };

  const labelFor = (plugin: string) => labelForCategory(categoryFor(plugin));

  return {
    categoryFor,
    counts,
    labelFor,
    labelForCategory,
    options,
    selected,
  };
}

export function scopeMappings<T extends TaxonomyMapping>(
  mappings: T[],
  categoryById: Map<string, TaxonomyCategory>,
  scope: CategoryScope,
): T[] {
  if (scope.kind === "all") return mappings;
  if (scope.kind === "uncategorized") {
    return mappings.filter(mapping => !categoryById.has(mapping.category_id));
  }
  return mappings.filter(mapping => mapping.category_id === scope.id);
}

export function filterMappings<T extends TaxonomyMapping>(
  mappings: T[],
  categoryById: Map<string, TaxonomyCategory>,
  search: string,
  kindFilter: string,
  language: AttackMethodNameLanguage = "en",
): T[] {
  const q = search.trim().toLowerCase();
  return mappings.filter(mapping => {
    if (kindFilter !== "all" && mapping.executor_kind !== kindFilter) return false;
    if (!q) return true;
    const category = categoryById.get(mapping.category_id);
    return attackMethodSearchText(mapping.executor_name, language).toLowerCase().includes(q)
      || mapping.executor_kind.toLowerCase().includes(q)
      || (mapping.technical_category ?? "").toLowerCase().includes(q)
      || (category?.name ?? "").toLowerCase().includes(q)
      || (category?.alias ?? "").toLowerCase().includes(q);
  });
}
