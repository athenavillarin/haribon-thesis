import React from 'react';
import { createPortal } from 'react-dom';
import { FiArrowDown, FiArrowUp, FiMinus, FiX, FiChevronRight } from 'react-icons/fi';

const MIN_EFFECT = 0.1;
const STRONG_EFFECT = 0.5;
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function compare(anomaly, higher, lower, usual) {
  if (anomaly == null || Math.abs(anomaly) < 0.2) return { short: usual, long: usual };
  const word = anomaly > 0 ? higher : lower;
  return { short: word, long: Math.abs(anomaly) >= 0.6 ? `much ${word}` : word };
}

function ensoPhase(oni) {
  if (oni == null) return 'unknown';
  if (oni >= 0.5) return oni >= 1.5 ? 'strong El Niño' : 'El Niño';
  if (oni <= -0.5) return oni <= -1.5 ? 'strong La Niña' : 'La Niña';
  return 'neutral';
}

function formatMonth(yearMonth) {
  const [year, month] = String(yearMonth || '').split('-').map(Number);
  return year && month ? `${MONTHS[month - 1]} ${year}` : 'an earlier month';
}

function describeDriver(driver) {
  switch (driver.key) {
    case 'sea_temperature': {
      const c = compare(driver.anomaly_90d, 'warmer than usual', 'cooler than usual', 'near usual');
      return {
        label: 'Sea temperature',
        short: c.short === 'near usual' ? 'usual sea temperature' : `${c.short.split(' ')[0]} sea`,
        detail: `${capitalize(c.long)} for this site and month, over the last 90 days.`,
      };
    }
    case 'rainfall': {
      const c = compare(driver.anomaly_60d, 'wetter than usual', 'drier than usual', 'near usual');
      return {
        label: 'Rainfall',
        short: c.short === 'near usual' ? 'usual rainfall' : `${c.short.split(' ')[0]} weather`,
        detail: `${capitalize(c.long)} for this site and month, over the last 60 days.`,
      };
    }
    case 'enso': {
      const phase = ensoPhase(driver.oni);
      return {
        label: 'ENSO (El Niño / La Niña)',
        short: phase === 'neutral' ? 'neutral ENSO' : phase,
        detail: `${capitalize(phase)} conditions (ONI ${formatSigned(driver.oni)}, ${formatMonth(driver.oni_month)}).`,
      };
    }
    case 'season': {
      const month = MONTHS[(driver.month || 1) - 1];
      return {
        label: 'Time of year',
        short: 'time of year',
        detail: driver.contribution >= 0
          ? `Bans have been more common around ${month}.`
          : `Bans have been less common around ${month}.`,
      };
    }
    case 'ban_history': {
      const pct = Math.round((driver.ban_rate || 0) * 100);
      return {
        label: 'Ban history at this site',
        short: pct === 0 ? `no bans in ${driver.year}` : `bans in ${driver.year}`,
        detail: pct === 0
          ? `No shellfish ban recorded here in ${driver.year}.`
          : `Under a shellfish ban on ${pct}% of days in ${driver.year}.`,
      };
    }
    default:
      return { label: driver.key, short: driver.key, detail: '' };
  }
}

function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function formatSigned(value) {
  if (value == null) return 'N/A';
  return `${value > 0 ? '+' : ''}${Number(value).toFixed(1)}`;
}

function effectOf(contribution) {
  const size = Math.abs(contribution);
  if (size < MIN_EFFECT) return { text: 'Little effect', Icon: FiMinus, color: 'text-gray-500' };
  const verb = contribution > 0 ? 'raises' : 'lowers';
  return {
    text: size >= STRONG_EFFECT ? capitalize(verb) + ' risk' : `Slightly ${verb} risk`,
    Icon: contribution > 0 ? FiArrowUp : FiArrowDown,
    color: contribution > 0 ? 'text-[#B45309]' : 'text-[#3F6D72]',
  };
}

export default function ForecastDrivers({ drivers, locationName, dateLabel }) {
  const dialogRef = React.useRef(null);
  const main = drivers.filter((d) => Math.abs(d.contribution) >= MIN_EFFECT).slice(0, 3);
  const items = main.length > 0 ? main : drivers.slice(0, 1);

  const open = () => dialogRef.current?.showModal();
  const close = () => dialogRef.current?.close();

  return (
    <>
      <button
        type="button"
        onClick={open}
        className="w-full text-left text-xs text-gray-600 leading-relaxed pt-1.5 border-t border-gray-100 group"
      >
        <span className="font-semibold text-gray-800">Main drivers:</span>{' '}
        {items.map((d, idx) => {
          const { short } = describeDriver(d);
          const { Icon, color, text } = effectOf(d.contribution);
          return (
            <span key={d.key} className="whitespace-nowrap">
              {short}
              <Icon className={`inline ml-0.5 -mt-0.5 ${color}`} aria-label={text} />
              {idx < items.length - 1 && <span className="mx-1 text-gray-400">·</span>}
            </span>
          );
        })}
        <span className="ml-1.5 inline-flex items-center font-semibold text-[#3F6D72] group-hover:underline whitespace-nowrap">
          Details <FiChevronRight aria-hidden="true" />
        </span>
      </button>

      {createPortal(<dialog
        ref={dialogRef}
        onClick={(e) => e.target === dialogRef.current && close()}
        className="font-quicksand rounded-2xl p-0 w-[min(92vw,440px)] backdrop:bg-black/40 shadow-xl"
      >
        <div className="p-5">
          <div className="flex items-start justify-between gap-3 mb-3">
            <div>
              <h2 className="text-base font-bold text-gray-900">What's driving this forecast</h2>
              <p className="text-xs text-gray-600">{locationName}, {dateLabel}</p>
            </div>
            <button type="button" onClick={close} aria-label="Close" className="p-1 rounded-lg text-gray-500 hover:bg-gray-100">
              <FiX />
            </button>
          </div>

          <ul className="space-y-2">
            {drivers.map((d) => {
              const { label, detail } = describeDriver(d);
              const { Icon, color, text } = effectOf(d.contribution);
              return (
                <li key={d.key} className="bg-[#F8F9FA] rounded-xl p-3 border border-gray-100/80">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-[13px] font-semibold text-gray-800">{label}</span>
                    <span className={`text-[11px] font-bold flex items-center gap-1 shrink-0 ${color}`}>
                      <Icon aria-hidden="true" /> {text}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5">{detail}</p>
                </li>
              );
            })}
          </ul>

          <div className="mt-3 space-y-1.5 text-[11px] text-gray-600 leading-relaxed">
            <p>
              Effects are from the logistic regression in the forecast ensemble, compared with an average day. The
              LSTM, GRU and Transformer models use the same inputs but cannot be broken down this way.
            </p>
            <p>
              ENSO uses the Oceanic Niño Index from 3 months back, the latest available when the forecast runs. It is
              the same for every site.
            </p>
            <p>
              Of the readings under Current Conditions, only sea temperature and rainfall are model inputs. The rest
              are shown for reference.
            </p>
          </div>
        </div>
      </dialog>, document.body)}
    </>
  );
}
