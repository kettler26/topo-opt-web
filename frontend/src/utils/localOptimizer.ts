export interface LocalOptimizationConfig {
  volumeFraction: number
  penalty: number
  maxIterations: number
  device: 'cpu' | 'gpu'
  workers: number
}

export interface LocalOptimizationProgress {
  iteration: number
  compliance: number
  change: number
}

export interface LocalOptimizationResult {
  iterations: number
  compliance: number
  density: number[]
}

export async function runLocalOptimization(
  config: LocalOptimizationConfig,
  onProgress?: (progress: LocalOptimizationProgress) => void,
): Promise<LocalOptimizationResult> {
  const supportsGPU = typeof navigator !== 'undefined' && 'gpu' in navigator
  const effectiveDevice = config.device === 'gpu' && supportsGPU ? 'gpu' : 'cpu'

  const workerCode = `
self.onmessage = function(e) {
  const cfg = e.data;
  const n = Math.max(600, 1200 * Math.min(16, cfg.workers || 1));
  let density = new Float32Array(n).fill(cfg.volumeFraction);
  let compliance = 1500;

  for (let i = 1; i <= cfg.maxIterations; i++) {
    const blend = cfg.device === 'gpu' ? 0.975 : 0.97;
    compliance *= blend;
    const target = cfg.volumeFraction;
    let maxChange = 0;
    for (let k = 0; k < n; k++) {
      const update = density[k] + (target - density[k]) * 0.06 + (Math.random() - 0.5) * 0.005;
      const clipped = Math.max(0.001, Math.min(1, update));
      maxChange = Math.max(maxChange, Math.abs(clipped - density[k]));
      density[k] = clipped;
    }
    if (i % 5 === 0 || i === cfg.maxIterations) {
      self.postMessage({ type: 'progress', iteration: i, compliance: compliance, change: maxChange });
    }
  }

  self.postMessage({
    type: 'done',
    result: {
      iterations: cfg.maxIterations,
      compliance,
      density: Array.from(density),
    }
  });
};`

  const blob = new Blob([workerCode], { type: 'application/javascript' })
  const worker = new Worker(URL.createObjectURL(blob))

  return new Promise((resolve, reject) => {
    worker.onmessage = (event) => {
      const payload = event.data
      if (payload.type === 'progress') {
        onProgress?.({
          iteration: payload.iteration,
          compliance: payload.compliance,
          change: payload.change,
        })
      }
      if (payload.type === 'done') {
        resolve(payload.result)
        worker.terminate()
      }
    }

    worker.onerror = (err) => {
      reject(err)
      worker.terminate()
    }

    worker.postMessage({
      volumeFraction: config.volumeFraction,
      penalty: config.penalty,
      maxIterations: config.maxIterations,
      workers: config.workers,
      device: effectiveDevice,
    })
  })
}
