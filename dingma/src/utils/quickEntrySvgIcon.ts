/**
 * 快捷入口图标：管理端常为 RemixIcon 类名（ri-xxx），小程序端仅能渲染 DingMa iconfont。
 * 将后端值规范为已与「我的」页菜单一致的单色可染色字形键（linggan2 / book / send2 等同源字形）。
 */

/** iconfont.css 中已定义的短键（不含前缀） */
const KNOWN_GLYPHS = new Set([
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

/** 后端若直接使用 Remix 全称（常见于管理端录入）→ 字形键 */
const REMIX_SUFFIX_EXACT = new Map<string, string>([
  ['book-line', 'book'],
  ['book-fill', 'book'],
  ['file-list-line', 'book'],
  ['file-list-fill', 'book'],
  ['file-text-line', 'book'],
  ['draft-line', 'book'],
  ['article-line', 'book'],
  ['folder-line', 'book'],
  ['clipboard-line', 'book'],
  ['t-shirt-line', 'industry'],
  ['graduation-cap-line', 'process'],
  ['medal-line', 'process'],
  ['database-line', 'knowledge'],
  ['database-fill', 'knowledge'],
  ['stack-line', 'works'],
  ['layers-line', 'works'],
  ['coins-line', 'works'],
  ['lightbulb-line', 'linggan2'],
  ['lightbulb-fill', 'linggan2'],
  ['flashlight-line', 'linggan2'],
  ['send-plane-line', 'send2'],
  ['send-plane-fill', 'send2'],
  ['share-forward-line', 'send2'],
  ['megaphone-line', 'notice'],
  ['megaphone-fill', 'notice'],
  ['notification-line', 'notice'],
  ['volume-up-line', 'notice'],
  ['user-smile-line', 'agent'],
  ['robot-line', 'agent'],
  ['robot-fill', 'agent'],
  ['account-circle-line', 'agent'],
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
  if (keyLower === 'linggan' || keyLower === 'linggan3') return 'linggan2'
  if (keyLower === 'send') return 'send2'
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

  /** 语义关键词兜底（与设计稿类目接近即可，避免空白字形） */
  const joined = ` ${stemLower.replace(/-/g, ' ')} `

  if (/(lightbulb|bulb|flashlight|ideas|brain)/.test(joined)) return 'linggan2'
  if (/(megaphone|notification|speaker|announce|bullhorn|volume)/.test(joined)) return 'notice'
  if (/(send|share-plane|telegram|flight)/.test(joined)) return 'send2'
  if (/(book|file|doc|folder|draft|article|notebook|sticky|memo|paper)/.test(joined)) return 'book'
  if (/(database|server|layers|coin|cylinder|stack|hard-drive|hosts)/.test(joined))
    return 'knowledge'
  if (/(tshirt|cloth|shopping|shopping-bag|store|shirt|dress)/.test(joined))
    return 'industry'
  if (/(graduation|education|school|degree|teacher|study|course)/.test(joined))
    return 'process'
  if (/(robot|user|account|smile|contact|women|men|badge|human)/.test(joined))
    return 'agent'
  if (/(pencil|edit|compose|quill|paint)/.test(joined)) return 'edit'

  return 'book'
}

/**
 * @param iconClassRaw 可为空；或与后台一致： icon-book / book / ri-book-line 等
 * @returns 传给 SvgIcon 的 `name`（无 icon- 前缀）
 */
export function quickEntrySvgGlyph(iconClassRaw: string | undefined | null): string {
  let s = stripIconPrefix(iconClassRaw ?? '').toLowerCase()
  if (!s) return 'linggan2'

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

  /** 不识别的短名：兜底为书单字形，避免出现空框 */
  return 'book'
}
