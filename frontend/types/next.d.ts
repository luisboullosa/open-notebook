/* Precise minimal typings for Next modules used in this project. */

declare module 'next' {
  // Minimal NextConfig placeholder to allow untyped configs.
  export type NextConfig = Record<string, any>
  const _default: any
  export default _default
}

declare module 'next/font/google' {
  export type FontResult = { className: string }
  export function Inter(options?: { subsets?: string[]; variable?: string } | any): FontResult
  export default Inter
}

declare module 'next/image' {
  import * as React from 'react'

  export interface StaticImageData {
    src: string
    height: number
    width: number
    blurDataURL?: string
  }

  export type StaticImport = StaticImageData | string

  export interface ImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    src: StaticImport
    width?: number
    height?: number
    alt?: string
    priority?: boolean
    fill?: boolean
    placeholder?: 'blur' | 'empty'
    blurDataURL?: string
  }

  const Image: React.FC<ImageProps>
  export default Image
}

declare module 'next/link' {
  import * as React from 'react'

  export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
    href: string
    prefetch?: boolean
    replace?: boolean
    scroll?: boolean
    shallow?: boolean
    locale?: string | false
  }

  const Link: React.FC<LinkProps>
  export default Link
}

declare module 'next/navigation' {
  export function usePathname(): string
  export function useRouter(): {
    push(url: string, options?: { scroll?: boolean; replace?: boolean } | any): void
    replace(url: string, options?: { scroll?: boolean } | any): void
    back(): void
  }
  export function useParams(): Record<string, string>
  export function redirect(url: string): void
  export function useSearchParams(): URLSearchParams
}

declare module 'next/dynamic' {
  import * as React from 'react'
  export default function dynamic<T = any>(
    importer: any,
    options?: { ssr?: boolean; loading?: React.ComponentType<any> }
  ): React.ComponentType<T>
}
