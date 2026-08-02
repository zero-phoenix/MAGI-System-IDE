const NATIVE_HOST = "com.magi.ide";

// P21.b.2: Cuatro flujos (Enviar a MAGI, Selección, Captura, Continuar aquí)

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "magi_send_selection",
    title: "Enviar selección a MAGI",
    contexts: ["selection"]
  });
  chrome.contextMenus.create({
    id: "magi_capture",
    title: "Capturar como evidencia para MAGI",
    contexts: ["page"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "magi_send_selection") {
    sendToNativeHost({
      action: "send_selection",
      text: info.selectionText,
      url: tab.url,
      title: tab.title
    });
  } else if (info.menuItemId === "magi_capture") {
    sendToNativeHost({
      action: "request_capture",
      url: tab.url
    });
  }
});

chrome.action.onClicked.addListener((tab) => {
  // Acción "Enviar a MAGI"
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText
  }, (results) => {
    let content = "";
    if (results && results[0]) content = results[0].result;
    
    sendToNativeHost({
      action: "send_page",
      url: tab.url,
      title: tab.title,
      content: content
    });
  });
});

function sendToNativeHost(payload) {
  chrome.runtime.sendNativeMessage(NATIVE_HOST, payload, (response) => {
    if (chrome.runtime.lastError) {
      console.error("Error conectando con MAGI:", chrome.runtime.lastError.message);
      return;
    }
    console.log("Respuesta de MAGI:", response);
  });
}
