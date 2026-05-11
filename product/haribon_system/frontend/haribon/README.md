# HARIBON v2.0 Frontend

A modern, clean React frontend for the HARIBON red tide prediction system, built with Tailwind CSS.

## Features

- **Clean, Modern UI**: Built with Tailwind CSS for a professional look
- **Interactive Dashboard**: Real-time red tide risk monitoring with map visualization
- **SeaStats Analytics**: Advanced environmental data analysis and trends
- **Comprehensive FAQs**: User-friendly information about red tide and the system
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Fast Performance**: Built with Vite for optimal development and production performance

## Tech Stack

- **React 19**: Latest React with modern hooks and features
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **React Router**: Client-side routing for navigation
- **Leaflet**: Interactive maps for location visualization
- **Axios**: HTTP client for API communication
- **Vite**: Fast build tool and development server

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd product/haribon_system/frontend/haribon
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and visit `http://localhost:5174`

### Backend Connection

The frontend connects to the HARIBON backend API running on `http://127.0.0.1:8001`. Make sure the backend is running before using the frontend.

## Project Structure

```
src/
├── components/
│   ├── Layout.jsx              # Main layout with sidebar navigation
│   └── dashboard/
│       ├── ForecastStrip.jsx   # Risk forecast cards
│       ├── MapSection.jsx      # Interactive map component
│       └── RightDashboard.jsx  # Location details panel
├── context/
│   └── LocationContext.jsx     # Global location state management
├── pages/
│   ├── Dashboard.jsx           # Main dashboard page
│   ├── SeaStats.jsx            # Analytics and trends page
│   └── FAQs.jsx                # Frequently asked questions
├── services/
│   └── api.js                  # API service layer
├── assets/                     # Static assets (logos, icons)
├── App.jsx                     # Main app component with routing
├── main.jsx                    # App entry point
└── index.css                   # Global styles with Tailwind
```

## Color Scheme

The application uses a consistent color scheme matching the original HARIBON branding:

- **Primary Dark**: `#203537` (sidebar, headers)
- **Risk Colors**:
  - Green (Very Low): `#2ECC71`
  - Yellow (Low): `#F1C40F`
  - Orange (Moderate): `#E67E22`
  - Red (High): `#E74C3C`
- **Background**: `#f7f8f9`
- **Text Colors**: Various grays for hierarchy

## Key Components

### Layout
- Fixed sidebar navigation with logo
- Responsive design that adapts to screen size
- Clean typography using Quicksand font

### Dashboard
- **Forecast Strip**: Horizontal scrollable cards showing all locations
- **Interactive Map**: Leaflet-based map with location markers
- **Details Panel**: Risk assessment and recommendations for selected location

### SeaStats
- Environmental parameter monitoring
- Location selection interface
- Placeholder for advanced analytics (charts, trends)

### FAQs
- Expandable question-answer format
- Contact information for support
- Professional layout with HARIBON branding

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `GET /api/forecast/latest` - Get all location forecasts
- `GET /api/forecast/locations` - Get location list
- `GET /api/forecast/risk-summary` - Get risk distribution summary
- `POST /api/forecast/trigger-update` - Trigger data refresh

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style

- Uses modern React patterns (hooks, functional components)
- Tailwind CSS for styling (no custom CSS files)
- Consistent component structure and naming
- Proper error handling and loading states

## Deployment

1. Build the application:
   ```bash
   npm run build
   ```

2. The `dist` folder contains the production-ready files

3. Serve the `dist` folder with any static file server

## Contributing

This frontend maintains the same functionality as the original HARIBON system while providing a much cleaner, more maintainable codebase with modern development practices.
