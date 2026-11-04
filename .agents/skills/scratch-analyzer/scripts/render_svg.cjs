const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const args = process.argv.slice(2);
  if (args.length < 2 || args.length > 3 || (args[2] && !['en','zh-tw'].includes(args[2])))
    throw Error('Usage: node tools/render_svg.cjs INPUT.txt OUTPUT.svg [en|zh-tw]');
  const [input, output, language = 'zh-tw'] = args;
  const code = fs.readFileSync(input, 'utf8');
  const scratchblocksRoot = path.dirname(require.resolve('scratchblocks/package.json'));
  const locale = JSON.parse(fs.readFileSync(path.join(scratchblocksRoot, 'locales/zh-tw.json'), 'utf8'));
  const chrome = process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {channel:'chrome'};
  const browser = await chromium.launch({headless:true, ...chrome});
  try {
    const page = await browser.newPage();
    await page.setContent('<!doctype html><meta charset="utf-8">');
    await page.addScriptTag({path:path.join(scratchblocksRoot,'build/scratchblocks.min.js')});
    const result = await page.evaluate(({code, locale, language}) => {
      scratchblocks.loadLanguages({'zh-tw':locale});
      const doc = scratchblocks.parse(code,{languages:['en']});
      const unknown = [];
      function visit(v) {
        if (!v || typeof v !== 'object') return;
        if (v.info && v.info.category === 'obsolete') unknown.push(v.info);
        if (language === 'zh-tw' && v.info) {
          const menus = {
            MOTION_POINTTOWARDS: {'mouse-pointer':'滑鼠游標'},
            CONTROL_CREATECLONEOF: {'myself':'自己'},
            SENSING_TOUCHINGOBJECT: {'edge':'邊緣','mouse-pointer':'滑鼠游標'},
            LOOKS_CHANGEEFFECTBY: {
              color:'顏色', fisheye:'魚眼', whirl:'旋轉', pixelate:'像素',
              mosaic:'馬賽克', brightness:'亮度', ghost:'幻影',
            },
          };
          const names = menus[v.info.id];
          const input = names && v.children.find(child => child.isInput);
          if (input && Object.hasOwn(names, input.value)) {
            input.value = names[input.value];
            input.menu = input.value;
            input.label = new scratchblocks.Label(input.value, `literal-${input.shape}`);
          }
        }
        if (language === 'zh-tw' && v.info && v.info.id === 'SENSING_OF') {
          const property = v.children.find(child => child.isInput);
          const names = {'costume #':'造型編號'};
          if (!property || !names[property.value]) throw Error('Unsupported sensing property translation: ' + (property && property.value));
          property.value = names[property.value];
          property.menu = property.value;
          property.label = new scratchblocks.Label(property.value, `literal-${property.shape}`);
        }
        for (const key of ['scripts','blocks','children']) if (Array.isArray(v[key])) v[key].forEach(visit);
      }
      visit(doc);
      if (unknown.length) throw Error('Unrecognized blocks: ' + JSON.stringify(unknown));
      if (language === 'zh-tw') doc.translate(scratchblocks.allLanguages['zh-tw']);
      const view = scratchblocks.newView(doc,{style:'scratch3',scale:1});
      view.render();
      return view.exportSVGString();
    }, {code, locale, language});
    fs.writeFileSync(output,result,'utf8');
    console.log('SVG written:',output, '('+language+')');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
