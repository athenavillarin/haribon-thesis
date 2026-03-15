import React, { useState } from 'react';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';
import logoImage from '../assets/logo.svg';

export default function FAQs() {
  const [openFAQ, setOpenFAQ] = useState(null);

  const toggleFAQ = (index) => {
    setOpenFAQ(openFAQ === index ? null : index);
  };

  return (
    <div className="min-h-full bg-haribon-bg p-6 pb-4 pr-5">
      <div className="w-full flex flex-col gap-3">
        <div className="mb-1">
          <h1 className="text-[28px] font-bold text-gray-800 leading-tight">About HARIBON</h1>
          <p className="text-sm text-gray-500 mt-1">AI-Powered Red Tide Detection and Forecasting for Western Visayas</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-3">
          <div className="rounded-xl border border-gray-200 bg-[#F3F4F6] p-5">
            <div className="flex items-start justify-between gap-3 mb-4">
              <h2 className="text-xl font-semibold text-gray-800">What is HARIBON?</h2>
              <span className="text-xs text-gray-500 text-right">Harmful Algal Bloom Intelligent Observer Network</span>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed mb-4">
              HARIBON is an AI-powered early warning system that detects and forecasts red tide risk levels across priority coastal areas in Western Visayas. The system provides daily, region-specific alerts to protect public health, support fisherfolk livelihoods, and inform local policy and marine resource management.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1 text-xs rounded-full border border-gray-200 text-gray-600 bg-white">Daily Forecast</span>
              <span className="px-3 py-1 text-xs rounded-full border border-gray-200 text-gray-600 bg-white">Interactive Map</span>
              <span className="px-3 py-1 text-xs rounded-full border border-gray-200 text-gray-600 bg-white">Risk Factors and Recommendations</span>
              <span className="px-3 py-1 text-xs rounded-full border border-gray-200 text-gray-600 bg-white">SeaStats Analytics</span>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-[#F3F4F6] p-5 flex items-center justify-center">
            <img src={logoImage} alt="HARIBON Logo" className="w-full max-w-[220px] h-auto" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_2.1fr] gap-3">
          <div className="rounded-xl border border-gray-200 bg-[#F3F4F6] p-5">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-xl font-semibold text-gray-800">Mission</h3>
              <span className="text-xs text-gray-500">Why we built HARIBON</span>
            </div>
            <p className="text-sm text-gray-600 mb-2">Deliver timely, accessible red tide risk information that safeguards:</p>
            <ul className="text-sm text-gray-600 list-disc pl-5 space-y-1">
              <li>Food safety and public health</li>
              <li>Fisherfolk income and aquaculture operations</li>
              <li>Marine ecosystems and local biodiversity</li>
            </ul>
          </div>

          <div className="rounded-xl border border-gray-200 bg-[#F3F4F6] p-5">
            <div className="flex items-start justify-between mb-3">
              <h3 className="text-xl font-semibold text-gray-800">Impact on Communities</h3>
              <span className="text-xs text-gray-500">People and Ecosystem</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
              <div>
                <span className="inline-flex px-2 py-0.5 rounded-full text-[11px] bg-white border border-gray-200 text-gray-500 mb-2">Fisherfolk and Aquaculture</span>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Plan harvesting around risk windows</li>
                  <li>Reduce income losses from sudden closures</li>
                  <li>Adopt precautionary measures during elevated risk</li>
                </ul>
              </div>
              <div>
                <span className="inline-flex px-2 py-0.5 rounded-full text-[11px] bg-white border border-gray-200 text-gray-500 mb-2">Public Health</span>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Issue timely advisories against shellfish consumption</li>
                  <li>Focus sampling and lab tests where risk is highest</li>
                </ul>
              </div>
              <div>
                <span className="inline-flex px-2 py-0.5 rounded-full text-[11px] bg-white border border-gray-200 text-gray-500 mb-2">Marine Ecosystem</span>
                <ul className="list-disc pl-5 space-y-1">
                  <li>Monitor seasonal patterns to inform protection</li>
                  <li>Support long-term management and policy decisions</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-[#F3F4F6] p-5">
          <div className="flex items-start justify-between mb-3">
            <h2 className="text-2xl font-bold text-gray-800">Frequently Asked Questions</h2>
            <span className="text-xs text-gray-500 pt-1">Answers to common questions about HARIBON</span>
          </div>

          <div className="space-y-2">
            {faqs.map((faq, index) => (
              <FAQItem
                key={index}
                faq={faq}
                isOpen={openFAQ === index}
                onToggle={() => toggleFAQ(index)}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function FAQItem({ faq, isOpen, onToggle }) {
  return (
    <div className="bg-[#F8F9FA] rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 text-left flex justify-between items-center hover:bg-white transition-colors"
      >
        <h3 className="text-lg font-medium text-gray-800 pr-4">{faq.question}</h3>
        {isOpen ? (
          <FiChevronUp className="text-gray-500 flex-shrink-0" />
        ) : (
          <FiChevronDown className="text-gray-500 flex-shrink-0" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 pb-4 pt-1 border-t border-gray-200 bg-white">
          <p className="text-gray-600 leading-relaxed text-sm">{faq.answer}</p>
        </div>
      )}
    </div>
  );
}

const faqs = [
  {
    question: "What is red tide and why is it dangerous?",
    answer: "Red tide refers to harmful algal blooms that can produce toxins, leading to shellfish poisoning and fish kills. Ingesting contaminated shellfish can cause severe illness. HARIBON helps communities avoid exposure by forecasting risk levels daily."
  },
  {
    question: "Which areas are covered?",
    answer: "Western Visayas priority AOIs, including Gigantes Islands (Carles, Iloilo), Roxas City, and Sapian Bay, Batan Bay, Pilar, and President Roxas. Coverage can expand as more boundaries and historical records are added."
  },
  {
    question: "How accurate is the forecast?",
    answer: "Accuracy depends on data quality and environmental variability. We train and validate the XGBoost model on historical bulletins and satellite-derived features, and we continually refine with new observations. Users should treat 'High' and 'Elevated' levels as precautionary signals and follow official advisories from BFAR and LGUs."
  },
  {
    question: "How often are forecasts updated?",
    answer: "Daily. A scheduled service fetches the latest satellite data, runs the model, and updates the dashboard so users can check current conditions each day."
  },
  {
    question: "How are risk levels defined?",
    answer: "Risk levels are derived from the model's predicted probability and mapped into four categories: Green (Very Low), Yellow (Low), Orange (Moderate), and Red (High). The dashboard also displays contributing conditions (e.g., chl-a proxy, SST, salinity, rainfall, land use signals) and recommended actions for each level."
  },
  {
    question: "What data sources are used?",
    answer: "HARIBON was developed by the University of the Philippines Visayas (UPV) in collaboration with the Bureau of Fisheries and Aquatic Resources (BFAR) and other partners. It leverages AI and satellite data to provide timely information on red tide risks."
  },
  {
    question: "Can I use dashboard offline?",
    answer: "No. Internet access is required to retrieve the latest forecasts and visualizations. You can, however, export or screenshot relevant summaries for offline reference."
  },
  {
    question: "Who maintains HARIBON?",
    answer: "HARIBON is developed by the Badminton Girls team from West Visayas State University. We welcome collaboration with LGUs, BFAR, and partner institutions to extend data coverage and improve model performance."
  },
  {
    question: "How can I report a suspected bloom or data issue?",
    answer: "Please contact your local BFAR office or submit reports through the dashboard's feedback form, including any available images or observations."
  }
];