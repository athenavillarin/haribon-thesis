import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { BsGrid } from 'react-icons/bs';
import { FiTrendingUp, FiInfo } from 'react-icons/fi';
import logoImage from '../assets/logo.svg';

export default function Layout() {
  const location = useLocation();

  return (
    <div className="h-screen w-screen max-w-screen overflow-x-hidden bg-[#F8F9FA] font-quicksand flex">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-[280px] bg-[#F3F4F6] flex flex-col justify-between overflow-hidden z-20 border-r border-gray-200">
        {/* Logo */}
        <div className="p-8 pb-8 flex justify-center">
          <img src={logoImage} alt="Haribon Project Logo" className="w-32 h-auto" />
        </div>

        {/* Navigation */}
        <nav className="px-6 flex-1 mt-8">
          <Link
            to="/"
            className={`flex items-center gap-4 px-6 py-3.5 text-base font-medium rounded-xl mb-3 transition-colors ${
              location.pathname === "/" 
                ? "bg-haribon-dark text-white shadow-lg shadow-gray-200" 
                : "text-gray-500 hover:bg-white hover:text-gray-800 hover:shadow-sm"
            }`}
          >
            <BsGrid className="text-xl" />
            <span>Dashboard</span>
          </Link>
          <Link
            to="/seastats"
            className={`flex items-center gap-4 px-6 py-3.5 text-base font-medium rounded-xl mb-3 transition-colors ${
              location.pathname === "/seastats" 
                ? "bg-haribon-dark text-white shadow-lg shadow-gray-200" 
                : "text-gray-500 hover:bg-white hover:text-gray-800 hover:shadow-sm"
            }`}
          >
            <FiTrendingUp className="text-xl" />
            <span>SeaStats</span>
          </Link>
          <Link
            to="/faqs"
            className={`flex items-center gap-4 px-6 py-3.5 text-base font-medium rounded-xl mb-3 transition-colors ${
              location.pathname === "/faqs" 
                ? "bg-haribon-dark text-white shadow-lg shadow-gray-200" 
                : "text-gray-500 hover:bg-white hover:text-gray-800 hover:shadow-sm"
            }`}
          >
            <FiInfo className="text-xl" />
            <span>FAQs</span>
          </Link>
        </nav>

        {/* Footer */}
        <div className="p-8 text-xs text-gray-400 leading-relaxed border-t border-gray-200 m-6 text-center">
          <h4 className="font-bold text-haribon-dark mb-1">Western Visayas</h4>
          <p>AI-Powered Red Tide Detection & Forecasting</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-[280px] p-8 h-screen overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}