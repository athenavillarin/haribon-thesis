import React, { useEffect, useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { BsGrid } from 'react-icons/bs';
import { FiTrendingUp, FiInfo, FiMenu, FiX } from 'react-icons/fi';
import logoImage from '../assets/logo.svg';
import logoMobileImage from '../assets/logo2.svg';

export default function Layout() {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = isMobileMenuOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: BsGrid },
    { to: '/seastats', label: 'SeaStats', icon: FiTrendingUp },
    { to: '/faqs', label: 'FAQs', icon: FiInfo },
  ];

  const renderNavLinks = () => (
    <>
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.to;

        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={() => setIsMobileMenuOpen(false)}
            className={`flex items-center gap-4 px-6 py-3.5 text-base font-medium rounded-xl mb-3 transition-colors ${
              isActive
                ? 'bg-haribon-dark text-white shadow-lg shadow-gray-200'
                : 'text-gray-500 hover:bg-white hover:text-gray-800 hover:shadow-sm'
            }`}
          >
            <Icon className="text-xl" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </>
  );

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-[#F8F9FA] font-quicksand flex">
      {/* Desktop Sidebar */}
      <aside className="fixed left-0 top-0 hidden h-full w-[280px] bg-[#F3F4F6] flex-col justify-between overflow-hidden border-r border-gray-200 lg:flex">
        {/* Logo */}
        <div className="p-8 pb-8 flex justify-center">
          <img src={logoImage} alt="Haribon Project Logo" className="w-32 h-auto" />
        </div>

        {/* Navigation */}
        <nav className="px-6 flex-1 mt-8">
          {renderNavLinks()}
        </nav>

        {/* Footer */}
        <div className="p-8 text-xs text-gray-400 leading-relaxed border-t border-gray-200 m-6 text-center">
          <h4 className="font-bold text-haribon-dark mb-1">Western Visayas</h4>
          <p>AI-Powered Red Tide Detection & Forecasting</p>
        </div>
      </aside>

      {/* Mobile Top Bar */}
      <header className="fixed left-0 top-0 z-[2600] flex h-[82px] w-full items-center justify-between bg-[#F8F9FA] px-5 pb-2 pt-4 lg:hidden">
        <img src={logoMobileImage} alt="Haribon Project Logo" className="w-[122px] h-auto" />
        <button
          type="button"
          aria-label={isMobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          onClick={() => setIsMobileMenuOpen((open) => !open)}
          className="inline-flex items-center justify-center text-gray-700"
        >
          {isMobileMenuOpen ? <FiX className="text-[22px]" /> : <FiMenu className="text-[22px]" />}
        </button>
      </header>

      {/* Mobile Drawer */}
      <div
        className={`fixed inset-0 z-[3100] transition-all duration-300 lg:hidden ${
          isMobileMenuOpen ? 'visible bg-black/25' : 'invisible bg-transparent'
        }`}
        onClick={() => setIsMobileMenuOpen(false)}
      >
        <aside
          className={`h-full w-[72%] max-w-[290px] bg-[#F3F4F6] flex flex-col justify-between border-r border-gray-200 transition-transform duration-300 ${
            isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
          onClick={(event) => event.stopPropagation()}
        >
          <div>
            <div className="px-6 pb-8 pt-7 flex justify-start">
              <img src={logoImage} alt="Haribon Project Logo" className="w-32 h-auto" />
            </div>
            <nav className="px-3">{renderNavLinks()}</nav>
          </div>

          <div className="px-6 pb-8 text-center">
            <h4 className="font-bold text-haribon-dark mb-1">Western Visayas</h4>
            <p className="text-sm text-[#2f4d51]">AI-Powered Red Tide Detection & Forecasting</p>
          </div>
        </aside>
      </div>

      {/* Main Content */}
      <main className="flex-1 lg:ml-[280px] min-h-screen overflow-y-auto pt-[82px] lg:pt-0">
        <Outlet />
      </main>
    </div>
  );
}