"""
Stealth Configuration - Конфигурация для обхода обнаружения автоматизации браузера.

Этот модуль предоставляет функции для настройки браузера Playwright
таким образом, чтобы минимизировать возможность обнаружения автоматизации.
"""
import logging
from typing import Dict, Any

from playwright.async_api import BrowserContext


logger = logging.getLogger(__name__)


async def apply_stealth_settings(context: BrowserContext) -> None:
    """
    Применяет настройки стелс-режима к контексту браузера.
    
    Args:
        context: Контекст браузера Playwright
    """
    logger.info("Применение настроек стелс-режима")
    
    try:
        # Добавляем JavaScript для модификации объекта navigator
        await context.add_init_script(js_navigator_modifications)
        
        # Скрываем WebDriver
        await context.add_init_script(js_hide_webdriver)
        
        # Модифицируем метод доступа к canvas fingerprinting
        await context.add_init_script(js_canvas_fingerprint_protection)
        
        # Скрываем модификации automation
        await context.add_init_script(js_hide_automation)
        
        # Исправляем несоответствие между navigator.languages и Accept-Language заголовком
        await context.add_init_script(js_fix_languages)
        
        # Скрываем selenium и webdriver свойства
        await context.add_init_script(js_hide_selenium)
        
        # Добавляем fake plugins
        await context.add_init_script(js_add_fake_plugins)
        
        # Добавляем стандартные шрифты для обхода font fingerprinting
        await context.add_init_script(js_add_standard_fonts)
        
        # Скрываем automation в отладочных свойствах Chrome
        await context.add_init_script(js_hide_chrome_automation)
        
        logger.info("Настройки стелс-режима успешно применены")
    
    except Exception as e:
        logger.error(f"Ошибка при применении настроек стелс-режима: {str(e)}")
        raise


# JavaScript для модификации объекта navigator
js_navigator_modifications = """
() => {
  // Переопределяем характеристики navigator для обхода fingerprinting
  const modifyNavigator = () => {
    // Оригинальный геттер свойства userAgent
    const originalUserAgentGetter = Object.getOwnPropertyDescriptor(Navigator.prototype, 'userAgent').get;
    
    // Переопределяем свойства navigator с использованием Object.defineProperty
    Object.defineProperties(Navigator.prototype, {
      'webdriver': {
        get: () => false,
        configurable: true
      },
      'language': {
        get: () => 'ru-RU',
        configurable: true
      },
      'languages': {
        get: () => ['ru-RU', 'ru', 'en-US', 'en'],
        configurable: true
      },
      'deviceMemory': {
        get: () => 8,
        configurable: true
      },
      'hardwareConcurrency': {
        get: () => 8,
        configurable: true
      },
      'cookieEnabled': {
        get: () => true,
        configurable: true
      },
      'appVersion': {
        get: function () {
          return originalUserAgentGetter.call(this).replace('Headless', '');
        },
        configurable: true
      },
      'platform': {
        get: () => 'Win32',
        configurable: true
      },
      'plugins': {
        get: function() {
          return {
            length: 5,
            refresh: () => {},
            item: (index) => { return null; },
            namedItem: (name) => { return null; },
            [Symbol.iterator]: function* () {
              const plugins = [
                {
                  name: 'Chrome PDF Plugin',
                  filename: 'internal-pdf-viewer',
                  description: 'Portable Document Format'
                },
                {
                  name: 'Chrome PDF Viewer',
                  filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                  description: ''
                },
                {
                  name: 'Native Client',
                  filename: 'internal-nacl-plugin',
                  description: ''
                }
              ];
              for (let i = 0; i < plugins.length; i++) {
                yield plugins[i];
              }
            }
          };
        },
        configurable: true
      }
    });
  };
  
  modifyNavigator();
}
"""

# JavaScript для скрытия WebDriver
js_hide_webdriver = """
() => {
  // Скрываем все признаки WebDriver
  Object.defineProperty(navigator, 'webdriver', {
    get: () => false,
    configurable: true
  });
  
  // Удаляем свойство navigator.webdriver из прототипа
  if (navigator.webdriver) {
    delete Navigator.prototype.webdriver;
  }
  
  // Скрываем переменную window.cdc_adoQpoasnfa76pfcZLmcfl_Array
  if (window.cdc_adoQpoasnfa76pfcZLmcfl_Array) {
    window.cdc_adoQpoasnfa76pfcZLmcfl_Array = undefined;
  }
  
  // Скрываем переменную window.cdc_adoQpoasnfa76pfcZLmcfl_Promise
  if (window.cdc_adoQpoasnfa76pfcZLmcfl_Promise) {
    window.cdc_adoQpoasnfa76pfcZLmcfl_Promise = undefined;
  }
  
  // Скрываем переменную window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol
  if (window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol) {
    window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol = undefined;
  }
}
"""

# JavaScript для защиты от canvas fingerprinting
js_canvas_fingerprint_protection = """
() => {
  // Оригинальный метод для создания данных изображения
  const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
  const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
  const originalToBlob = HTMLCanvasElement.prototype.toBlob;
  
  // Изменяем результат незначительно, чтобы избежать обнаружения
  CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {
    const imageData = originalGetImageData.call(this, sx, sy, sw, sh);
    
    // Вносим небольшие модификации в данные пикселей
    // Это делает отпечаток canvas уникальным, но визуально неотличимым
    if (imageData && imageData.data && imageData.data.length > 0) {
      // Модифицируем только несколько пикселей
      const l = imageData.data.length;
      // Изменяем некоторые пиксели рандомно, но незначительно
      for (let i = 0; i < 10; i++) {
        const pos = Math.floor(Math.random() * l);
        if (imageData.data[pos] < 254) {
          imageData.data[pos] += 1;
        }
      }
    }
    
    return imageData;
  };
  
  // Модифицируем метод toDataURL
  HTMLCanvasElement.prototype.toDataURL = function() {
    // Если вызов происходит от FingerprintJS или аналогичных инструментов
    const callStack = new Error().stack || '';
    if (callStack.includes('Fingerprint') || 
        callStack.includes('fingerprint') || 
        callStack.includes('CanvasFingerprint')) {
      // Возвращаем слегка модифицированную версию
      const result = originalToDataURL.apply(this, arguments);
      // Вставляем случайный символ где-то в данные
      const position = result.length - Math.floor(Math.random() * 20) - 20;
      return result.substring(0, position) + 'A' + result.substring(position + 1);
    }
    // Иначе возвращаем оригинальный результат
    return originalToDataURL.apply(this, arguments);
  };
  
  // Модифицируем метод toBlob, если он используется
  HTMLCanvasElement.prototype.toBlob = function() {
    const callStack = new Error().stack || '';
    if (callStack.includes('Fingerprint') || 
        callStack.includes('fingerprint') || 
        callStack.includes('CanvasFingerprint')) {
      // Небольшая задержка в несколько мс для блокировки синхронных вызовов
      const start = Date.now();
      while (Date.now() - start < 5) {}
    }
    // Вызываем оригинальный метод
    return originalToBlob.apply(this, arguments);
  };
}
"""

# JavaScript для скрытия признаков автоматизации
js_hide_automation = """
() => {
  // Скрываем признаки automation
  const originalFunction = window.navigator.permissions.query;
  
  // Переопределяем функцию permissions.query
  window.navigator.permissions.query = (parameters) => {
    // Проверяем, запрашивают ли разрешения для автоматизации
    if (parameters.name === 'notifications' || 
        parameters.name === 'clipboard-read' || 
        parameters.name === 'clipboard-write') {
      return originalFunction(parameters);
    }
    
    // Если запрос касается "медия-устройств" или автоматизации, имитируем запрет
    if (parameters.name === 'midi' || parameters.name === 'midi-sysex' || 
        parameters.name === 'media-device-information' || 
        parameters.name === 'geolocation' || 
        parameters.name === 'automation') {
      return Promise.resolve({ state: 'prompt', onchange: null });
    }
    
    // Для всех остальных случаев используем оригинальную функцию
    return originalFunction(parameters);
  };
  
  // Переопределяем navigator.permissions.query для Playwright
  if (navigator.permissions) {
    const oldQuery = navigator.permissions.query;
    navigator.permissions.__proto__.query = function(parameters) {
      if (parameters.name === 'notifications') {
        return Promise.resolve({ state: Notification.permission, onchange: null });
      }
      return oldQuery.call(navigator.permissions, parameters);
    };
  }
  
  // Фиксируем функцию определения Headless Chrome
  const newProto = navigator.__proto__;
  delete newProto.webdriver;
  navigator.__proto__ = newProto;
}
"""

# JavaScript для исправления несоответствия языков
js_fix_languages = """
() => {
  // Исправляем несоответствие между navigator.languages и Accept-Language заголовком
  Object.defineProperty(navigator, 'languages', {
    get: function() {
      return ['ru-RU', 'ru', 'en-US', 'en'];
    }
  });
}
"""

# JavaScript для скрытия Selenium и WebDriver
js_hide_selenium = """
() => {
  // Скрываем признаки Selenium
  // Проверяем, есть ли свойства _selenium, _Selenium_IDE_Recorder, _selenium_unwrapped
  const seleniumProperties = [
    '_selenium', 
    '_Selenium_IDE_Recorder', 
    '_selenium_unwrapped',
    '__webdriver_script_fn',
    '__driver_evaluate',
    '__webdriver_evaluate',
    '__selenium_evaluate',
    '__fxdriver_evaluate',
    '__driver_unwrapped',
    '__webdriver_unwrapped',
    '__selenium_unwrapped',
    '__fxdriver_unwrapped',
    '__webdriver_script_func',
    '$cdc_asdjflasutopfhvcZLmcfl_'
  ];
  
  // Удаляем свойства, связанные с Selenium
  for (const prop of seleniumProperties) {
    if (window[prop]) {
      delete window[prop];
    }
    
    // Используем defineProperty для предотвращения последующего добавления
    Object.defineProperty(window, prop, {
      get: () => undefined,
      set: () => true,
      configurable: false
    });
  }
  
  // Проверка на window.document.$cdc_asdjflasutopfhvcZLmcfl_
  if (window.document.$cdc_asdjflasutopfhvcZLmcfl_) {
    delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
  }
}
"""

# JavaScript для добавления fake plugins
js_add_fake_plugins = """
() => {
  // Создаем fake MimeType и Plugin для имитации реального браузера
  const makeFakeMimeType = (mimeType, description, suffixes, extension) => ({
    type: mimeType,
    description,
    suffixes,
    __proto__: MimeType.prototype
  });
  
  const makeFakePlugin = (name, description, mimeTypes) => {
    const plugin = {
      name,
      description,
      length: mimeTypes.length,
      __proto__: Plugin.prototype
    };
    
    // Добавляем каждый MimeType в плагин
    mimeTypes.forEach((mimeType, index) => {
      plugin[index] = mimeType;
      plugin[mimeType.type] = mimeType;
    });
    
    return plugin;
  };
  
  // Создаем fake MimeTypes
  const pdfMimeType = makeFakeMimeType(
    'application/pdf', 
    'Portable Document Format', 
    'pdf', 
    'pdf'
  );
  
  const chromePDFMimeType = makeFakeMimeType(
    'application/x-google-chrome-pdf', 
    'Portable Document Format', 
    'pdf', 
    'pdf'
  );
  
  const naclMimeType = makeFakeMimeType(
    'application/x-nacl', 
    'Native Client Executable', 
    '', 
    ''
  );
  
  const pnaclMimeType = makeFakeMimeType(
    'application/x-pnacl', 
    'Portable Native Client Executable', 
    '', 
    ''
  );
  
  // Создаем fake Plugins
  const chromePDFPlugin = makeFakePlugin(
    'Chrome PDF Plugin', 
    'Portable Document Format', 
    [pdfMimeType, chromePDFMimeType]
  );
  
  const chromePDFViewerPlugin = makeFakePlugin(
    'Chrome PDF Viewer', 
    '', 
    [pdfMimeType]
  );
  
  const nativeClientPlugin = makeFakePlugin(
    'Native Client', 
    '', 
    [naclMimeType, pnaclMimeType]
  );
  
  // Создаем fake PluginArray и MimeTypeArray
  const fakePlugins = [chromePDFPlugin, chromePDFViewerPlugin, nativeClientPlugin];
  const fakeMimeTypes = [pdfMimeType, chromePDFMimeType, naclMimeType, pnaclMimeType];
  
  // Переопределяем navigator.plugins и navigator.mimeTypes
  Object.defineProperty(navigator, 'plugins', {
    get: function() {
      const pluginArray = Object.create(PluginArray.prototype);
      
      Object.defineProperty(pluginArray, 'length', {
        value: fakePlugins.length,
        writable: false,
        enumerable: true
      });
      
      fakePlugins.forEach((plugin, index) => {
        Object.defineProperty(pluginArray, index, {
          value: plugin,
          writable: false,
          enumerable: true
        });
        
        Object.defineProperty(pluginArray, plugin.name, {
          value: plugin,
          writable: false,
          enumerable: false
        });
      });
      
      // Добавляем методы refresh, item, namedItem
      Object.defineProperty(pluginArray, 'refresh', {
        value: function() {},
        writable: false,
        enumerable: false
      });
      
      Object.defineProperty(pluginArray, 'item', {
        value: function(index) {
          return this[index];
        },
        writable: false,
        enumerable: false
      });
      
      Object.defineProperty(pluginArray, 'namedItem', {
        value: function(name) {
          return this[name];
        },
        writable: false,
        enumerable: false
      });
      
      return pluginArray;
    },
    enumerable: true,
    configurable: true
  });
  
  // Переопределяем navigator.mimeTypes
  Object.defineProperty(navigator, 'mimeTypes', {
    get: function() {
      const mimeTypeArray = Object.create(MimeTypeArray.prototype);
      
      Object.defineProperty(mimeTypeArray, 'length', {
        value: fakeMimeTypes.length,
        writable: false,
        enumerable: true
      });
      
      fakeMimeTypes.forEach((mimeType, index) => {
        Object.defineProperty(mimeTypeArray, index, {
          value: mimeType,
          writable: false,
          enumerable: true
        });
        
        Object.defineProperty(mimeTypeArray, mimeType.type, {
          value: mimeType,
          writable: false,
          enumerable: false
        });
      });
      
      // Добавляем методы item, namedItem
      Object.defineProperty(mimeTypeArray, 'item', {
        value: function(index) {
          return this[index];
        },
        writable: false,
        enumerable: false
      });
      
      Object.defineProperty(mimeTypeArray, 'namedItem', {
        value: function(name) {
          return this[name];
        },
        writable: false,
        enumerable: false
      });
      
      return mimeTypeArray;
    },
    enumerable: true,
    configurable: true
  });
}
"""

# JavaScript для добавления стандартных шрифтов
js_add_standard_fonts = """
() => {
  // Имитируем стандартные шрифты для обхода font fingerprinting
  const fontFaceSetPrototype = FontFaceSet.prototype;
  const originalCheck = fontFaceSetPrototype.check;
  
  // Стандартные шрифты, которые должны быть "установлены"
  const standardFonts = [
    'Arial', 'Arial Black', 'Arial Narrow', 'Arial Rounded MT Bold', 'Calibri',
    'Cambria', 'Cambria Math', 'Comic Sans MS', 'Courier', 'Courier New',
    'Georgia', 'Helvetica', 'Impact', 'Lucida Console', 'Lucida Sans Unicode',
    'Microsoft Sans Serif', 'Palatino Linotype', 'Segoe UI', 'Tahoma',
    'Times', 'Times New Roman', 'Trebuchet MS', 'Verdana'
  ];
  
  // Переопределяем метод check для FontFaceSet
  fontFaceSetPrototype.check = function() {
    const font = arguments[0];
    
    // Извлекаем имя шрифта из аргумента
    let fontName;
    if (typeof font === 'string') {
      // Формат: 'bold 12px Arial'
      const parts = font.split(' ');
      fontName = parts[parts.length - 1].toLowerCase().replace(/['"]/g, '');
    } else if (font instanceof FontFace) {
      fontName = font.family.toLowerCase().replace(/['"]/g, '');
    }
    
    // Проверяем, является ли шрифт стандартным
    const isStandardFont = standardFonts.some(
      f => f.toLowerCase() === fontName
    );
    
    if (isStandardFont) {
      return true;
    }
    
    // Для нестандартных шрифтов используем оригинальный метод
    return originalCheck.apply(this, arguments);
  };
}
"""

# JavaScript для скрытия признаков Chrome автоматизации
js_hide_chrome_automation = """
() => {
  // Скрываем отладочные свойства, характерные для автоматизации Chrome
  if (window.chrome) {
    // Если debugger доступен в объекте chrome, его скрывают
    if (window.chrome.debugger) {
      window.chrome.debugger = undefined;
    }
    
    // Создаем фейковый объект для runtime
    if (!window.chrome.runtime) {
      window.chrome.runtime = {};
    }
    
    // Заменяем метод sendMessage
    window.chrome.runtime.sendMessage = function() {
      return { message: "success" };
    };
    
    // Добавляем chrome.loadTimes() для более полной эмуляции
    if (!window.chrome.loadTimes) {
      window.chrome.loadTimes = function() {
        return {
          firstPaintTime: 0,
          firstPaintAfterLoadTime: 0,
          requestTime: Date.now() / 1000,
          startLoadTime: Date.now() / 1000,
          commitLoadTime: Date.now() / 1000,
          finishDocumentLoadTime: Date.now() / 1000,
          finishLoadTime: Date.now() / 1000,
          firstPaintAfterLoadTimeMS: 0,
          navigationType: "Other",
          wasFetchedViaSpdy: false,
          wasNpnNegotiated: false,
          npnNegotiatedProtocol: "unknown",
          wasAlternateProtocolAvailable: false,
          connectionInfo: "unknown"
        };
      };
    }
    
    // Добавляем chrome.csi() для полноты
    if (!window.chrome.csi) {
      window.chrome.csi = function() {
        return {
          onloadT: Date.now(),
          pageT: Date.now() - performance.timing.navigationStart,
          startE: Date.now(),
          tran: 15
        };
      };
    }
  }
}
"""
