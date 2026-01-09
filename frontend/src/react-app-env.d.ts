/// <reference types="react-scripts" />

declare module 'react-icons/fi' {
  import { ComponentType, SVGProps } from 'react';
  
  type IconType = ComponentType<SVGProps<SVGSVGElement>> & { displayName?: string };
  
  export const FiHome: IconType;
  export const FiUsers: IconType;
  export const FiDollarSign: IconType;
  export const FiBook: IconType;
  export const FiPlus: IconType;
  export const FiSearch: IconType;
  export const FiEdit: IconType;
  export const FiTrendingUp: IconType;
  export const FiCheckCircle: IconType;
  export const FiXCircle: IconType;
  export const FiUser: IconType;
  export const FiSave: IconType;
  export const FiX: IconType;
  export const FiLoader: IconType;
  export const FiCheck: IconType;
  export const FiFilter: IconType;
  export const FiAlertCircle: IconType;
  export const FiEdit2: IconType;
}
