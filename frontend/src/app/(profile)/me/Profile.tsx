"use client";

import React, { JSX } from "react";

import {PersonalSection} from "@/app/(profile)/me/sections/PersonalSection";
import {GiftsSection} from "./sections/GiftsSection";
import {TokensSection} from "./sections/TokensSection";
import {InvestmentsSection} from "./sections/InvestmentsSection/InvestmentsSection";

export const Profile = (): JSX.Element => {
  console.log("[Profile Render] Proceeding to render profile content.");

  return (
    <>
      <PersonalSection />
      {/*<InvestmentsSection/>*/}
      {/*<TokensSection/>*/}
      {/*<GiftsSection/>*/}
    </>
  );
};
