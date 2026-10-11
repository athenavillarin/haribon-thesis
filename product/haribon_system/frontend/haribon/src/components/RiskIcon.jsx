import React from 'react';
import { HugeiconsIcon } from '@hugeicons/react';
import { getRiskHugeicon } from './riskStyles';

export function RiskIcon({ riskColor, size = 16, className = '' }) {
  const icon = getRiskHugeicon(riskColor);
  return <HugeiconsIcon icon={icon} size={size} className={className} />;
}

export default RiskIcon;
