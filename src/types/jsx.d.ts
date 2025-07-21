/// <reference types="react" />
/// <reference types="react-dom" />

declare global {
  namespace JSX {
    interface Element extends React.ReactElement<any, any> { }
    interface ElementClass extends React.Component<any> {
      render(): React.ReactNode
    }
    interface ElementAttributesProperty {
      props: {}
    }
    interface ElementChildrenAttribute {
      children: {}
    }
    interface IntrinsicElements {
      [elem: string]: any
      div: any
      span: any
      button: any
      input: any
      h1: any
      h2: any
      h3: any
      h4: any
      h5: any
      h6: any
      p: any
      img: any
      a: any
      form: any
      label: any
      textarea: any
      select: any
      option: any
      ul: any
      li: any
      nav: any
      header: any
      footer: any
      section: any
      article: any
      aside: any
      main: any
    }
  }

  // Make React components more permissive
  declare module 'react' {
    interface FC<P = {}> {
      (props: P): any
    }
    interface FunctionComponent<P = {}> {
      (props: P): any
    }
  }
}

export {}
