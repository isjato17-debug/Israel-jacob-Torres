import type { Language } from "../journey-api";
export const CHOICES: Record<Exclude<Language, "en">, Record<string, string>> = {
  es: { LLC: "LLC (responsabilidad limitada)", Corporation: "Corporación", Partnership: "Sociedad", Nonprofit: "Organización sin fines de lucro", "Sole proprietorship": "Empresa individual", "Independent business": "Empresa independiente", "Holding company": "Sociedad matriz (holding)", Subsidiary: "Empresa subsidiaria" },
  zh: { LLC: "LLC（有限责任公司）", Corporation: "公司", Partnership: "合伙企业", Nonprofit: "非营利组织", "Sole proprietorship": "个人独资企业", "Independent business": "独立企业", "Holding company": "控股公司", Subsidiary: "子公司" },
  ar: { LLC: "LLC (شركة ذات مسؤولية محدودة)", Corporation: "شركة مساهمة", Partnership: "شراكة", Nonprofit: "منظمة غير ربحية", "Sole proprietorship": "منشأة فردية", "Independent business": "عمل مستقل", "Holding company": "شركة قابضة", Subsidiary: "شركة تابعة" },
  hi: { LLC: "LLC (सीमित देयता कंपनी)", Corporation: "कॉर्पोरेशन", Partnership: "साझेदारी", Nonprofit: "गैर-लाभकारी संगठन", "Sole proprietorship": "एकल स्वामित्व", "Independent business": "स्वतंत्र व्यवसाय", "Holding company": "होल्डिंग कंपनी", Subsidiary: "सहायक कंपनी" },
  sw: { LLC: "LLC (kampuni yenye dhima ndogo)", Corporation: "Shirika", Partnership: "Ubia", Nonprofit: "Shirika lisilo la faida", "Sole proprietorship": "Umiliki wa mtu mmoja", "Independent business": "Biashara huru", "Holding company": "Kampuni mama", Subsidiary: "Kampuni tanzu" },
};
