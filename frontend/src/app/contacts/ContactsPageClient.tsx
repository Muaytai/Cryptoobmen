"use client";

import {useEffect, useState} from "react";
import {useTheme} from "@/lib/ThemeProvider";
const ContactsPageClient = () => {
  const {theme} = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    if (typeof document !== "undefined") {
      setIsDarkMode(document.documentElement.classList.contains("dark"));
    }
  }, [theme]);

  return (
    <div
      className={`${
        isDarkMode ? "bg-[#111014] text-white" : "bg-white text-gray-900"
      } min-h-screen`}
    >
      <div className="max-w-6xl mx-auto px-4 py-12">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-center">
          Наши{" "}
          <span
            className={`${
              isDarkMode ? "text-violet-400" : "text-violet-600"
            }`}
          >
            контакты
          </span>
        </h1>

        {/* Контент контактов пока используется из серверного компонента */} 
      </div>
    </div>
  );
};

export default ContactsPageClient;



