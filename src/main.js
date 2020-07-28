import Hello from './Hello.svelte';

const router = {Hello};

export default function(appId, props = {}, target = null) {
  const appClass = router[appId];
  const app = new appClass({
    target: document.querySelector(target || '#anchor'),
    props: props
  });
}
