# DocumentProcessing.Dashboard

This .NET Aspire solution orchestrates the complete Document Processing platform, including:

- **DocumentProcessing.Dashboard** - Blazor Web App for the main dashboard interface
- **document-processor** - Python FastAPI service for document processing
- **knowledge-loader** - Next.js application for knowledge management

## Prerequisites

- .NET 10.0 SDK or later
- Python 3.x with `uv` package manager
- Node.js and npm
- .NET Aspire workload installed

To install the .NET Aspire workload:
```bash
dotnet workload install aspire
```

To trust the .NET development certificates:
```bash
dotnet dev-certs https --trust
```

## Project Structure

```
dashboard/
├── DocumentProcessing.Dashboard/           # Blazor Web App
├── DocumentProcessing.Dashboard.AppHost/   # Aspire AppHost orchestrator
├── DocumentProcessing.Dashboard.ServiceDefaults/  # Shared service configurations
└── DocumentProcessing.Dashboard.sln        # Solution file
```

## Getting Started

### Running the Solution

The AppHost will automatically start all three applications together:

```bash
cd src/dashboard
dotnet run --project DocumentProcessing.Dashboard.AppHost
```

This will:
1. Start the Python FastAPI app on port 8000
2. Start the Next.js app on port 3000
3. Start the Blazor dashboard
4. Launch the Aspire Dashboard for monitoring and management

### Accessing the Applications

Once running, you can access:
- **Aspire Dashboard**: Typically at http://localhost:15000 (check console output)
- **Blazor Dashboard**: Port assigned by Aspire
- **Document Processor API**: http://localhost:8000
- **Knowledge Loader**: http://localhost:3000

The Aspire Dashboard provides:
- Real-time monitoring of all services
- Logs from all applications in one place
- Resource usage metrics
- Distributed tracing
- Easy navigation between services

## Configuration

### Python App Requirements

The Python FastAPI app uses `uv` for dependency management and requires:
- A `.env` file in `src/document-processor/` (see `.env.example`)
- Dependencies installed in the virtual environment:
  ```bash
  cd ../document-processor
  uv pip install -r requirements.txt
  ```

**Note**: The Aspire AppHost is configured to use the existing virtual environment at `src/document-processor/.venv`. Make sure dependencies are installed before running the AppHost.

### Next.js App Setup

The Next.js app requires:
- Dependencies installed:
  ```bash
  cd ../knowledge-loader
  npm install
  ```
- Environment configuration in `.env.local` (see `.env.example`)

## Development

### Building the Solution

```bash
dotnet build DocumentProcessing.Dashboard.sln
```

### Running Individual Projects

While Aspire is recommended for running the complete solution, you can run projects individually:

**Blazor Dashboard:**
```bash
dotnet run --project DocumentProcessing.Dashboard
```

**Python FastAPI:**
```bash
cd ../document-processor
source .venv/bin/activate
python main.py
```

**Next.js App:**
```bash
cd ../knowledge-loader
npm run dev
```

## Aspire Features

This solution leverages .NET Aspire for:
- **Service Discovery**: Automatic discovery and communication between services
- **Health Checks**: Built-in health monitoring for all services
- **Telemetry**: Distributed tracing and metrics collection
- **Environment Management**: Consistent configuration across services
- **Developer Dashboard**: Unified view of all services and their status

## Learn More

- [.NET Aspire Documentation](https://learn.microsoft.com/dotnet/aspire/)
- [Blazor Documentation](https://learn.microsoft.com/aspnet/core/blazor/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
