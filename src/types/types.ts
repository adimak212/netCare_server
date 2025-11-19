import { Interface } from "readline";

export interface Dictionary<T> {
  [key: string]: T;
}

export type Component = {
  node_id: string;
  name: string;
  modelType: string;
  x: number;
  y: number;
  deviceType: number;
  ports: [];
};

export type LinkComp = {
  port: string;
  node_id: string;
  port_number: number;
  index: number;
  adapter_number: number;
};

export type Link = {
  link_id : string;
  from: LinkComp;
  to: LinkComp;
};