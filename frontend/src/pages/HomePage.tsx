export function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="text-center max-w-2xl">
        <h2 className="text-3xl font-bold text-foreground mb-4">
          Sibyl
        </h2>
        <p className="text-xl text-muted-foreground">
          Upload a sustainability report to begin analysis
        </p>
        <div className="mt-8 p-12 border-2 border-dashed border-border rounded-lg bg-card/50">
          <p className="text-muted-foreground">
            PDF upload coming in FRD 2
          </p>
        </div>
      </div>
    </div>
  );
}
