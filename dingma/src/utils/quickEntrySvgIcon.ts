/**
 * 快捷入口图标：管理端常为 RemixIcon 类名（ri-xxx），小程序端映射为 Lucide 矢量键或 iconfont 回退键。
 * 首页设计稿对齐：brain-circuit / sparkles / clapperboard / book-open / copy / megaphone / lightbulb。
 */

/** Lucide 键（SvgIcon 优先渲染）+ 仍走 iconfont 的短键 */
const KNOWN_GLYPHS = new Set([
  'brain-circuit',
  'megaphone',
  'sparkles',
  'clapperboard',
  'book-open',
  'copy',
  'lightbulb',
  'user-round-cog',
  'user',
  'linggan',
  'linggan2',
  'linggan3',
  'notice',
  'service',
  'shenjidaili',
  'works',
  'suanli',
  'send',
  'send2',
  'ready2',
  'tone',
  'industry',
  'target_audience',
  'agent',
  'qiehuan',
  'edit',
  'delete',
  'add',
  'book',
  'point',
  'hotspot',
  'knowledge',
  'process'
])

/** 后端若直接使用 Remix 全称（常见于管理端录入）→ Lucide / 字形键 */
const REMIX_SUFFIX_EXACT = new Map<string, string>([
  ['book-line', 'book-open'],
  ['book-fill', 'book-open'],
  ['book-open-line', 'book-open'],
  ['book-open-fill', 'book-open'],
  ['file-list-line', 'book-open'],
  ['file-list-fill', 'book-open'],
  ['file-text-line', 'book-open'],
  ['draft-line', 'book-open'],
  ['article-line', 'book-open'],
  ['folder-line', 'book-open'],
  ['clipboard-line', 'copy'],
  ['file-copy-line', 'copy'],
  ['file-copy-fill', 'copy'],
  ['sparkling-line', 'sparkles'],
  ['sparkling-fill', 'sparkles'],
  ['magic-line', 'sparkles'],
  ['clapperboard-line', 'clapperboard'],
  ['clapperboard-fill', 'clapperboard'],
  ['film-line', 'clapperboard'],
  ['video-line', 'clapperboard'],
  ['t-shirt-line', 'industry'],
  ['graduation-cap-line', 'process'],
  ['medal-line', 'process'],
  ['database-line', 'knowledge'],
  ['database-fill', 'knowledge'],
  ['stack-line', 'works'],
  ['layers-line', 'works'],
  ['coins-line', 'works'],
  ['lightbulb-line', 'lightbulb'],
  ['lightbulb-fill', 'lightbulb'],
  ['flashlight-line', 'lightbulb'],
  ['send-plane-line', 'send2'],
  ['send-plane-fill', 'send2'],
  ['share-forward-line', 'send2'],
  ['megaphone-line', 'megaphone'],
  ['megaphone-fill', 'megaphone'],
  ['notification-line', 'megaphone'],
  ['volume-up-line', 'megaphone'],
  ['brain-line', 'brain-circuit'],
  ['brain-circuit-line', 'brain-circuit'],
  ['user-smile-line', 'brain-circuit'],
  ['robot-line', 'brain-circuit'],
  ['robot-fill', 'brain-circuit'],
  ['account-circle-line', 'brain-circuit'],
  ['edit-line', 'edit'],
  ['pencil-line', 'edit']
])

function stripIconPrefix(raw: string): string {
  let s = raw.trim()
  if (s.startsWith('icon-')) {
    s = s.slice('icon-'.length).trim()
  }
  return s
}

function ensureMonoGlyphKey(keyLower: string): string {
  if (keyLower === 'linggan' || keyLower === 'linggan3') return 'lightbulb'
  if (keyLower === 'send') return 'send2'
  if (keyLower === 'notice') return 'megaphone'
  if (keyLower === 'agent') return 'brain-circuit'
  if (keyLower === 'book') return 'book-open'
  return keyLower
}

/**
 * Remix 形如：ri-book-line、ri-database-2-line，提取中间段落再匹配。
 */
function remixStemToGlyph(stemLower: string): string {
  /** 先试完整 stem（去掉 ri- 后整段），再试常见变体去掉末尾 line/fill */
  const candidates = [stemLower, stemLower.replace(/-fill$/, '-line')]
  const tryLookup = (k: string) => {
    const withLine = k.endsWith('-line') || k.endsWith('-fill') ? k : `${k}-line`
    return REMIX_SUFFIX_EXACT.get(withLine)
  }

  for (const c of candidates) {
    const hit = REMIX_SUFFIX_EXACT.get(c) ?? tryLookup(c)
    if (hit) return hit
  }

  /** 语义关键词兜底（与设计稿 Lucide 类目对齐） */
  const joined = ` ${stemLower.replace(/-/g, ' ')} `

  if (/(brain-circuit|brain circuit|chip|robot|account-circle)/.test(joined)) return 'brain-circuit'
  if (/(lightbulb|bulb|flashlight|ideas|brain)/.test(joined)) return 'lightbulb'
  if (/(megaphone|notification|speaker|announce|bullhorn|volume)/.test(joined)) return 'megaphone'
  if (/(sparkle|magic|star)/.test(joined)) return 'sparkles'
  if (/(clapper|film|video|movie)/.test(joined)) return 'clapperboard'
  if (/(copy|duplicate|clipboard)/.test(joined)) return 'copy'
  if (/(send|share-plane|telegram|flight)/.test(joined)) return 'send2'
  if (/(book-open|book open|notebook|open-book)/.test(joined)) return 'book-open'
  if (/(book|file|doc|folder|draft|article|sticky|memo|paper)/.test(joined)) return 'book-open'
  if (/(database|server|layers|coin|cylinder|stack|hard-drive|hosts)/.test(joined))
    return 'knowledge'
  if (/(tshirt|cloth|shopping|shopping-bag|store|shirt|dress)/.test(joined))
    return 'industry'
  if (/(graduation|education|school|degree|teacher|study|course)/.test(joined))
    return 'process'
  if (/(robot|user|account|smile|contact|women|men|badge|human)/.test(joined))
    return 'brain-circuit'
  if (/(pencil|edit|compose|quill|paint)/.test(joined)) return 'edit'

  return 'book-open'
}

/**
 * @param iconClassRaw 可为空；或与后台一致： icon-book / book / ri-book-line 等
 * @returns 传给 SvgIcon 的 `name`（无 icon- 前缀）
 */
export function quickEntrySvgGlyph(iconClassRaw: string | undefined | null): string {
  let s = stripIconPrefix(iconClassRaw ?? '').toLowerCase()
  if (!s) return 'brain-circuit'

  if (KNOWN_GLYPHS.has(s)) {
    return ensureMonoGlyphKey(s)
  }

  if (s.startsWith('ri-')) {
    const stem = s.slice(3).replace(/-fill$/, '-line').replace(/-bold$/, '-line')
    return remixStemToGlyph(stem)
  }

  /** 容错：偶有混写 riBookLine → 不适用；若看起来像 remix 后缀 */
  if (s.endsWith('-line') || s.endsWith('-fill')) {
    const stem = s.replace(/^ri-/, '')
    return remixStemToGlyph(stem)
  }

  /** 不识别的短名：兜底为设计稿默认字形 */
  return 'book-open'
}
