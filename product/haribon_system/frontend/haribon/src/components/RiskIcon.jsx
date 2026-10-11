import React from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import {
  CheckmarkCircle02Icon,
  Alert02Icon,
  Alert01Icon,
  AlertDiamondIcon,
} from '@hugeicons/core-free-icons';

export const getRiskHugeicon = (riskColor) => {
  const norm = (riskColor || '').toLowerCase();
  if (norm === 'red' || norm.includes('high')) return AlertDiamondIcon;
  if (norm === 'orange' || norm.includes('moderate')) return Alert01Icon;
  if (norm === 'yellow' || norm.includes('low')) return Alert02Icon;
  return CheckmarkCircle02Icon;
};

export function RiskIcon({ riskColor, size = 16, className = '' }) {
  const icon = getRiskHugeicon(riskColor);
  return <HugeiconsIcon icon={icon} size={size} className={className} />;
}

export function getRiskSvgString(riskColor, size = 14) {
  const iconData = getRiskHugeicon(riskColor);
  if (!Array.isArray(iconData)) return '';
  const innerHtml = iconData
    .map(([tag, attrs]) => {
      const attrStr = Object.entries(attrs)
        .filter(([k]) => k !== 'key')
        .map(([k, v]) => `${k}="${v}"`)
        .join(' ');
      return `<${tag} ${attrStr} />`;
    })
    .join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block; vertical-align:-0.125em;">${innerHtml}</svg>`;
}

export default RiskIcon;
