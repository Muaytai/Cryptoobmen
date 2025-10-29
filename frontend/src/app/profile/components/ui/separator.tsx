import * as SeparatorPrimitive from "@radix-ui/react-separator";
import * as React from "react";

import styles from "./separator.module.css";

const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root>
>(
  (
    { className = "", orientation = "horizontal", decorative = true, ...props },
    ref,
  ) => {
    return (
      <SeparatorPrimitive.Root
        ref={ref}
        decorative={decorative}
        orientation={orientation}
        className={[
          styles.separator,
          orientation === "horizontal" ? styles.horizontal : styles.vertical,
          className,
        ].join(" ")}
        {...props}
      />
    );
  },
);

Separator.displayName = SeparatorPrimitive.Root.displayName;

export { Separator };
