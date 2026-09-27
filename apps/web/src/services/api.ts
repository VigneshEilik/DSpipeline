const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
    request_id?: string;
  };
}

class ApiClient {
  private workspaceId: string | null = null;
  private token: string | null = null;

  setWorkspaceId(id: string) {
    this.workspaceId = id;
    if (typeof window !== "undefined") {
      localStorage.setItem("modelops_workspace_id", id);
    }
  }

  getWorkspaceId(): string | null {
    if (!this.workspaceId && typeof window !== "undefined") {
      this.workspaceId = localStorage.getItem("modelops_workspace_id");
    }
    return this.workspaceId;
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== "undefined") {
      sessionStorage.setItem("modelops_token", token);
    }
  }

  getToken(): string | null {
    if (!this.token && typeof window !== "undefined") {
      this.token = sessionStorage.getItem("modelops_token");
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const wsId = this.getWorkspaceId();
    if (wsId) {
      headers["X-Workspace-ID"] = wsId;
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: "omit",
    };

    const res = await fetch(url, config);
    const json: ApiResponse<T> = await res.json();

    if (!res.ok || json.success === false) {
      const errMsg = json.error?.message || json.message || `Request failed with status ${res.status}`;
      throw new Error(errMsg);
    }

    return json.data;
  }

  // Auth
  async bootstrapDev() {
    return this.request<any>("/auth/bootstrap-dev", { method: "POST" });
  }

  async getMe() {
    return this.request<any>("/auth/me");
  }

  // Datasets
  async getDatasets() {
    return this.request<any[]>("/datasets");
  }

  async getDataset(id: string) {
    return this.request<any>(`/datasets/${id}`);
  }

  async getDatasetPreview(id: string, page = 1, pageSize = 20) {
    return this.request<any>(`/datasets/${id}/preview?page=${page}&page_size=${pageSize}`);
  }

  async uploadDataset(formData: FormData) {
    const url = `${API_BASE}/datasets`;
    const headers: Record<string, string> = {};
    const token = this.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const wsId = this.getWorkspaceId();
    if (wsId) headers["X-Workspace-ID"] = wsId;

    const res = await fetch(url, {
      method: "POST",
      headers,
      body: formData,
    });
    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error?.message || "Upload failed");
    return json.data;
  }

  // Experiments
  async getExperiments() {
    return this.request<any[]>("/experiments");
  }

  async getExperiment(id: string) {
    return this.request<any>(`/experiments/${id}`);
  }

  async createExperiment(data: any) {
    return this.request<any>("/experiments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  // Models
  async getModels() {
    return this.request<any[]>("/models");
  }

  async getModel(id: string) {
    return this.request<any>(`/models/${id}`);
  }

  async registerModel(data: any) {
    return this.request<any>("/models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  async approveModel(modelId: string, data: any) {
    return this.request<any>(`/models/${modelId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  // Deployments
  async getDeployments() {
    return this.request<any[]>("/deployments");
  }

  async getDeployment(id: string) {
    return this.request<any>(`/deployments/${id}`);
  }

  async createDeployment(data: any) {
    return this.request<any>("/deployments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  async rollbackDeployment(id: string, data: any) {
    return this.request<any>(`/deployments/${id}/rollback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  // Predictions
  async predictSingle(features: any, deploymentId?: string) {
    return this.request<any>("/predictions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ features, deployment_id: deploymentId }),
    });
  }

  async getPredictions(limit = 50, offset = 0) {
    return this.request<any[]>(`/predictions?limit=${limit}&offset=${offset}`);
  }

  // Monitoring
  async getMonitoringOverview() {
    return this.request<any>("/monitoring/overview");
  }

  async getLatestDrift() {
    return this.request<any>("/monitoring/drift");
  }

  async runDrift(data = {}) {
    return this.request<any>("/monitoring/drift/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }

  // Workspaces
  async getWorkspace(id: string) {
    return this.request<any>(`/workspaces/${id}`);
  }

  async addMember(workspaceId: string, data: any) {
    return this.request<any>(`/workspaces/${workspaceId}/members`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();
