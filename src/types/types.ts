export type CanvasComponent = {
    id: string;
    type: 'router' | 'pc' | 'cloud' | 'switch';
    instanceId : number;
    name: string;
    node_type: string;
    x : number;
    y : number;
}
