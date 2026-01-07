# AI Virtual Try-On

An AI-powered virtual try-on application that lets you see how clothes look on you before buying. Simply take a photo of yourself and paste a link to any clothing item to see the magic happen.

## Features

- **Camera Capture**: Take a photo directly in the browser
- **Photo Upload**: Upload an existing photo of yourself
- **URL Input**: Paste links to clothing items from any website
- **Direct Upload**: Upload clothing images directly
- **AI Processing**: Uses advanced AI models for realistic virtual try-on
- **Download Results**: Save your virtual try-on images

## Getting Started

### Prerequisites

- Node.js 18+ installed
- npm or yarn package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-photo-app
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
```

4. Add your Replicate API token to `.env.local`:
```
REPLICATE_API_TOKEN=your_token_here
```

Get your API token at: https://replicate.com/account/api-tokens

### Running the App

Development mode:
```bash
npm run dev
```

Production build:
```bash
npm run build
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Demo Mode

The app works without an API key in demo mode - perfect for testing the UI flow. In demo mode, the original photo is returned instead of an AI-generated result.

## Usage

1. **Upload Your Photo**: Click to upload or use the camera button to take a photo
2. **Add Clothing**: Either:
   - Paste a URL to a clothing image
   - Upload a clothing image directly
3. **Generate**: Click "Generate Try-On" to see the result
4. **Download**: Save your virtual try-on image

## Tips for Best Results

- Use a front-facing photo with good lighting
- Stand straight with arms slightly away from your body
- Use clothing images with white or plain backgrounds
- Full-body photos work best for pants/dresses

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **AI**: Replicate API (IDM-VTON model)

## API Routes

- `POST /api/try-on`: Processes the virtual try-on request
- `POST /api/fetch-image`: Fetches images from external URLs (CORS proxy)

## License

MIT
