/**
 * 业务图标着色：SvgIcon/uview 均需显色，避免微信小程序下 inherit 发灰或无描边。
 * 首页 / 工作台快捷卡片：优先接口 bg_color 十六进制，否则按序号轮转印章色系。
 */

const SVG_ICON_VARIANTS: readonly string[] = ['#D94B36', '#C43D2A', '#B45309', '#A03322']

function normalizeHex(hex: string): string | null {
  let h = hex.trim().replace(/^#/, '')
  if (!h.length) return null
  if (h.length === 3) {
    h = h
      .split('')
      .map((ch) => ch + ch)
      .join('')
  }
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null
  return '#' + h.toUpperCase()
}

/**
 * @param bgColor 接口下发的背景色字符串（可为 null）
 * @param index   列表下标：无有效色时使用轮转色
 */
export function svgIconColorFromBg(bgColor: string | null | undefined, index: number): string {
  const fromApi = normalizeHex(bgColor ?? '')
  if (fromApi) return fromApi
  const i = Number.isFinite(index) && index >= 0 ? index : 0
  return SVG_ICON_VARIANTS[i % SVG_ICON_VARIANTS.length]
}
