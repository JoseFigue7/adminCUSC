import React from 'react';
import * as FiIcons from 'react-icons/fi';

// Wrapper para los iconos que funciona con React 19 y TypeScript
type IconProps = React.SVGProps<SVGSVGElement>;

// Helper para crear iconos con manejo de tipos
const createIcon = (iconName: string) => {
  return (props: IconProps) => {
    const IconComponent = (FiIcons as any)[iconName];
    if (!IconComponent) {
      console.warn(`Icon ${iconName} not found in react-icons/fi`);
      return null;
    }
    return React.createElement(IconComponent, props);
  };
};

export const FiHome: React.FC<IconProps> = createIcon('FiHome');
export const FiUsers: React.FC<IconProps> = createIcon('FiUsers');
export const FiDollarSign: React.FC<IconProps> = createIcon('FiDollarSign');
export const FiBook: React.FC<IconProps> = createIcon('FiBook');
export const FiPlus: React.FC<IconProps> = createIcon('FiPlus');
export const FiSearch: React.FC<IconProps> = createIcon('FiSearch');
export const FiEdit: React.FC<IconProps> = createIcon('FiEdit');
export const FiTrendingUp: React.FC<IconProps> = createIcon('FiTrendingUp');
export const FiCheckCircle: React.FC<IconProps> = createIcon('FiCheckCircle');
export const FiXCircle: React.FC<IconProps> = createIcon('FiXCircle');
export const FiUser: React.FC<IconProps> = createIcon('FiUser');
export const FiSave: React.FC<IconProps> = createIcon('FiSave');
export const FiX: React.FC<IconProps> = createIcon('FiX');
export const FiLoader: React.FC<IconProps> = createIcon('FiLoader');
export const FiCheck: React.FC<IconProps> = createIcon('FiCheck');
export const FiFilter: React.FC<IconProps> = createIcon('FiFilter');
export const FiAlertCircle: React.FC<IconProps> = createIcon('FiAlertCircle');
export const FiEdit2: React.FC<IconProps> = createIcon('FiEdit2');
export const FiFileText: React.FC<IconProps> = createIcon('FiFileText');
export const FiDownload: React.FC<IconProps> = createIcon('FiDownload');
export const FiUpload: React.FC<IconProps> = createIcon('FiUpload');
export const FiArrowLeft: React.FC<IconProps> = createIcon('FiArrowLeft');
export const FiArrowUp: React.FC<IconProps> = createIcon('FiArrowUp');
export const FiArrowDown: React.FC<IconProps> = createIcon('FiArrowDown');
export const FiAward: React.FC<IconProps> = createIcon('FiAward');
export const FiBarChart2: React.FC<IconProps> = createIcon('FiBarChart2');
export const FiCalendar: React.FC<IconProps> = createIcon('FiCalendar');
export const FiChevronLeft: React.FC<IconProps> = createIcon('FiChevronLeft');
export const FiChevronRight: React.FC<IconProps> = createIcon('FiChevronRight');
export const FiSun: React.FC<IconProps> = createIcon('FiSun');
export const FiMoon: React.FC<IconProps> = createIcon('FiMoon');
export const FiInfo: React.FC<IconProps> = createIcon('FiInfo');
export const FiLogIn: React.FC<IconProps> = createIcon('FiLogIn');
export const FiLogOut: React.FC<IconProps> = createIcon('FiLogOut');
export const FiUserPlus: React.FC<IconProps> = createIcon('FiUserPlus');
export const FiMail: React.FC<IconProps> = createIcon('FiMail');
export const FiPhone: React.FC<IconProps> = createIcon('FiPhone');
export const FiLock: React.FC<IconProps> = createIcon('FiLock');
export const FiPrinter: React.FC<IconProps> = createIcon('FiPrinter');
export const FiClock: React.FC<IconProps> = createIcon('FiClock');
export const FiAlertTriangle: React.FC<IconProps> = createIcon('FiAlertTriangle');
export const FiRefreshCw: React.FC<IconProps> = createIcon('FiRefreshCw');
export const FiCreditCard: React.FC<IconProps> = createIcon('FiCreditCard');
export const FiEye: React.FC<IconProps> = createIcon('FiEye');