export type CanvasComponent = {
    id: string;
    type: 'router' | 'pc' | 'cloud' | 'switch';
    instanceId : number;
    name: string;
}

export type NodeData = {
    name: string;
    node_type: string;
    compute_id: string;
    x: number;
    y: number;
}