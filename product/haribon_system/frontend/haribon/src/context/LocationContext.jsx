import React, { createContext, useContext, useState } from 'react';

const LocationContext = createContext();

export function LocationProvider({ children }) {
  const [selectedLocation, setSelectedLocation] = useState(null);

  return (
    <LocationContext.Provider value={{ selectedLocation, setSelectedLocation }}>
      {children}
    </LocationContext.Provider>
  );
}

export function useAppLocation() {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useAppLocation must be used within a LocationProvider');
  }
  return context;
}