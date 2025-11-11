import { Interface } from "readline";

export interface Dictionary<T> {
  [key: string]: T;
}

export type Component = {
  id: string;
  name: string;
  modelType: string;
  x: number;
  y: number;
  deviceType: number;
  ports: [];
};

export type LinkComp = {
  port: string;
  instanceId: number;
  port_number: number;
  index: number;
  adapter_number: number;
};

export type Link = {
  from: LinkComp;
  to: LinkComp;
};