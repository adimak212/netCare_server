class Device {
  id?: number;
  modelType?: string;
  icon?: string;
  x?: number;
  y?: number;
  deviceType?: "ethernet_switch" | "dynamips" | "vpcs" | "cloud";
  ports?: {
    link_type: string,
    port_number: number,
    short_name:string
  }[];
  takenPorts?: {
    takenPort: number;
    connectedTo: { port: string; device: Device; instanceId: number };
  }[] | undefined;
  name? : string;
}

class PC extends Device {
  constructor(id: number, x: number, y: number) {
    super();
    this.x = x;
    this.y = y;
    this.modelType = "";
    this.id = id;
    this.deviceType = "vpcs";
    this.ports = [{
      link_type: "ethernet",
      port_number: 0,
      short_name:"e0"
    }];
    this.name = "PC";
  }
}

class Switch extends Device {
  constructor(
    id: number,
    modelType: string,
    x: number,
    y: number,
    ports?: {
    link_type: string,
    port_number: number,
    short_name:string
  }[]
    
  ) {
    super();
    this.x = x;
    this.y = y;
    this.id = id;
    this.modelType = modelType;
    this.deviceType = "ethernet_switch";
    this.ports = ports;
    this.name = "Switch";
  }
 
}

class Router extends Device {
  constructor(
    id: number,
    modelType: string,
    x: number,
    y: number,
    ports?: {
    link_type: string,
    port_number: number,
    short_name:string
  }[]
  ) {
    super();
    this.x = x;
    this.y = y;
    this.id = id;
    this.modelType = modelType;
    this.deviceType = "dynamips";
    this.ports = ports;
    this.name = "Router";
  }
}

class Cloud extends Device {
  constructor(
    id: number, 
    x: number,
    y: number,
  ){
    super();
    this.x = x;
    this.y = y;
    this.id = id;
    this.ports =[{
      link_type: "ethernet",
      port_number: 0,
      short_name:"e0"
    }];
    this.deviceType = "cloud"
    this.modelType = ""
    this.name = "Cloud";
  }
}

export { Device, PC, Switch, Router , Cloud };