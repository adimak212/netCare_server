import mongoose, { Schema, Document, Model } from "mongoose";

export interface IProject extends Document {
  owner_id: string;
  name: string;
  project_id: string;
  GNS3_name:string;
}

const projectSchema: Schema<IProject> = new Schema({
  name: {
    type: String,
    required: true,
  },
  project_id: {
    type: String,
    required: true,
  },
  owner_id: {
    type: String,
    required : true
  },
  GNS3_name: {
    type: String,
    required : true,
    unique: true
  }
});
export const Project: Model<IProject> = mongoose.model<IProject>("projects", projectSchema);
