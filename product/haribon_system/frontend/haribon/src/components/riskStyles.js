import {
  CheckmarkCircle02Icon,
  AlertCircleIcon,
  Alert02Icon,
  AlertDiamondIcon,
} from '@hugeicons/core-free-icons';

// fill: map pins and other graphics. ink/tint: text and badges (AA contrast on light backgrounds).
export const RISK_STYLES = {
  green: { fill: '#00C853', ink: '#166534', tint: '#DCFCE7', border: '#BBF7D0' },
  yellow: { fill: '#FFB703', ink: '#854D0E', tint: '#FEF9C3', border: '#FDE68A' },
  orange: { fill: '#FF6B00', ink: '#9A3412', tint: '#FFEDD5', border: '#FED7AA' },
  red: { fill: '#EF233C', ink: '#991B1B', tint: '#FEE2E2', border: '#FECACA' },
  unknown: { fill: '#64748B', ink: '#374151', tint: '#F3F4F6', border: '#E5E7EB' },
};

export const SELECTED_ACCENT = '#3F6D72';

export const getRiskStyle = (riskColor) => RISK_STYLES[riskColor] || RISK_STYLES.unknown;

export const getRiskHugeicon = (riskColor) => {
  const norm = (riskColor || '').toLowerCase();
  if (norm === 'red' || norm.includes('high')) return AlertDiamondIcon;
  if (norm === 'orange' || norm.includes('moderate')) return Alert02Icon;
  if (norm === 'yellow' || norm.includes('low')) return AlertCircleIcon;
  return CheckmarkCircle02Icon;
};

const toKebab = (name) => name.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);

export function getRiskIconMarkup(riskColor, { strokeWidth } = {}) {
  const iconData = getRiskHugeicon(riskColor);
  if (!Array.isArray(iconData)) return '';
  return iconData
    .map(([tag, attrs]) => {
      const attrStr = Object.entries(attrs)
        .filter(([k]) => k !== 'key' && !(strokeWidth && k === 'strokeWidth'))
        .map(([k, v]) => `${toKebab(k)}="${v}"`)
        .join(' ');
      const width = strokeWidth ? ` stroke-width="${strokeWidth}"` : '';
      return `<${tag} ${attrStr}${width} />`;
    })
    .join('');
}

export function getRiskSvgString(riskColor, size = 14) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" style="display:inline-block; vertical-align:-0.125em;">${getRiskIconMarkup(riskColor)}</svg>`;
}
