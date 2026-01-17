import { Button } from "@/components/ui/button"

function App() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center gap-4">
      <h1 className="text-3xl font-bold text-foreground">AuditEng Dashboard</h1>
      <Button>Click me</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="destructive">Destructive</Button>
    </div>
  )
}

export default App
